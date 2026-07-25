# Tests/Infraestructura/Remoto/Integracion/test_hypervisor_servicer.py
"""
test_hypervisor_servicer.py — Integración: HypervisorServicer real
sobre un grpc.server SÍNCRONO real (ThreadPoolExecutor) — a diferencia
del resto de servicers del proyecto (que usan grpc.aio.server), el
Hypervisor corre síncrono (ver hypervisor_server.py). Por eso la
fixture `levantar_servidor` de conftest.py (pensada para grpc.aio) no
sirve aquí: un handler síncrono devuelto directamente a un servidor
aio rompe, porque el framework async intenta hacer `await` sobre lo
que devuelve el handler. Se define una fixture local equivalente pero
síncrona.

hypervisor_servicer.py no tenía NINGÚN test hasta ahora — solo se
probaba la clase Hypervisor en sí (test_hypervisor.py), nunca el
servicer + dispatch + serialización proto reales.
"""

from concurrent import futures

import grpc
import pytest

from Infraestructura.Gestores.Bots.Hypervisor.hypervisor import Hypervisor
from Infraestructura.Gestores.Bots.Hypervisor.hypervisor_servicer import (
    HypervisorServicer,
)
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    hypervisor_service_pb2 as pb,
    hypervisor_service_pb2_grpc as pb_grpc,
)


@pytest.fixture
def levantar_servidor_sincrono():
    """Análogo síncrono de la fixture `levantar_servidor` de
    conftest.py — ver docstring del módulo."""
    servidores = []

    def _levantar(registrar_fn):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
        registrar_fn(server)
        puerto = server.add_insecure_port("localhost:0")
        server.start()
        servidores.append(server)
        return f"localhost:{puerto}"

    yield _levantar

    for server in servidores:
        server.stop(grace=1)


class FakeProceso:
    """Proceso que nunca termina por sí solo — ver mismo patrón en
    test_hypervisor_acciones_delegadas.py."""

    def __init__(self):
        import threading

        self._nunca = threading.Event()

    def wait(self):
        self._nunca.wait()


class FakeLanzador:
    def lanzar(self, hypervisor_id, bot_id, codigo_gz, env_extra):
        return FakeProceso()

    def limpiar(self, hypervisor_id, bot_id):
        pass


class FakeGestorClient:
    def notificar_avatar_sin_piloto(self, bot_id):
        pass


@pytest.fixture
def cliente_hypervisor(levantar_servidor_sincrono):
    hv = Hypervisor(
        hypervisor_id="hv_test",
        gestor_client=FakeGestorClient(),
        capacity=2,
        lanzador_procesos=FakeLanzador(),
    )
    servicer = HypervisorServicer(hv)
    address = levantar_servidor_sincrono(
        lambda s: pb_grpc.add_HypervisorServiceServicer_to_server(servicer, s)
    )

    channel = grpc.insecure_channel(address)
    stub = pb_grpc.HypervisorServiceStub(channel)
    yield stub, hv
    channel.close()


@pytest.mark.integration
def test_spawn_bot_y_get_bot_stats_via_grpc(cliente_hypervisor):
    stub, _ = cliente_hypervisor
    cfg = common_pb2.BotConfig(bot_id="bot_1", budget=10)

    resp_spawn = stub.SpawnBot(pb.SpawnBotRequest(config=cfg))
    assert resp_spawn.ok is True

    resp_stats = stub.GetBotStats(pb.BotIdRequest(bot_id="bot_1"))
    assert resp_stats.points_left == 10


@pytest.mark.integration
def test_get_bot_stats_bot_desconocido_devuelve_not_found(cliente_hypervisor):
    stub, _ = cliente_hypervisor

    with pytest.raises(grpc.RpcError) as exc_info:
        stub.GetBotStats(pb.BotIdRequest(bot_id="no_existe"))

    assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND


@pytest.mark.integration
def test_freeze_y_resume_via_grpc(cliente_hypervisor):
    stub, _ = cliente_hypervisor

    resp_freeze = stub.Freeze(pb.FreezeRequest())
    assert resp_freeze.ok is True

    resp_resume = stub.Resume(pb.ResumeRequest())
    assert resp_resume.ok is True


@pytest.mark.integration
def test_reset_budgets_via_grpc_actualiza_puntos_reales(cliente_hypervisor):
    stub, _ = cliente_hypervisor
    stub.SpawnBot(
        pb.SpawnBotRequest(config=common_pb2.BotConfig(bot_id="bot_1", budget=10))
    )

    resp = stub.ResetBudgets(
        pb.ResetBudgetsRequest(bot_ids=["bot_1"], default_budget=50, overrides=[])
    )

    assert resp.ok is True
    stats = stub.GetBotStats(pb.BotIdRequest(bot_id="bot_1"))
    assert stats.points_left == 50


@pytest.mark.integration
def test_kill_bot_via_grpc(cliente_hypervisor):
    stub, _ = cliente_hypervisor
    stub.SpawnBot(
        pb.SpawnBotRequest(config=common_pb2.BotConfig(bot_id="bot_1", budget=10))
    )

    resp = stub.KillBot(pb.BotIdRequest(bot_id="bot_1"))

    assert resp.ok is True
    with pytest.raises(grpc.RpcError):
        stub.GetBotStats(pb.BotIdRequest(bot_id="bot_1"))
