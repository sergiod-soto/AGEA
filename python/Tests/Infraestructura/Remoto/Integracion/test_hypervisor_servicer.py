# Tests/Infraestructura/Remoto/Integracion/test_hypervisor_servicer.py
"""
test_hypervisor_servicer.py — Integración: HypervisorServicer real
sobre un grpc.aio.server real, golpeado con un stub async real.

ADAPTADO tras la migración de Hypervisor a asyncio (ver docstring de
hypervisor.py): antes este fichero montaba su PROPIA fixture con un
grpc.server SÍNCRONO + ThreadPoolExecutor, precisamente porque el
Hypervisor de entonces corría síncrono y HypervisorServicer no podía
vivir en un servidor async (un handler síncrono devuelto a un
framework async rompe, porque intenta hacer `await` sobre lo que
devuelve). Ahora que HypervisorServicer es `async def` de punta a
punta, ya no hace falta esa fixture aparte — se usa la
`levantar_servidor` compartida de conftest.py, igual que el resto de
servicers async del proyecto.
"""

import grpc.aio
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


class FakeProceso:
    """
    Doble de asyncio.subprocess.Process que nunca termina por sí
    solo — basta para spawn_bot()/GetBotStats(), que no necesitan que
    el proceso muera. `wait()` async (ver mismo patrón en
    test_hypervisor.py): un `threading.Event().wait()` aquí
    bloquearía el propio loop de eventos del servidor.
    """

    def __init__(self):
        import asyncio

        self._nunca = asyncio.Event()

    async def wait(self):
        await self._nunca.wait()

    def terminate(self):
        pass


class FakeLanzador:
    async def lanzar(self, hypervisor_id, bot_id, codigo_gz, env_extra):
        return FakeProceso()

    def limpiar(self, hypervisor_id, bot_id):
        pass


class FakeGestorClient:
    async def notificar_avatar_sin_piloto(self, bot_id):
        pass


@pytest.fixture
async def cliente_hypervisor(levantar_servidor):
    """
    Usa la fixture compartida levantar_servidor (grpc.aio real, puerto
    efímero) — HypervisorServicer ya no necesita el servidor síncrono
    especial que tenía antes. Al terminar el test se cancelan los
    watchers que hayan quedado vivos (bots spawneados cuyo FakeProceso
    nunca "muere" por sí solo).
    """
    hv = Hypervisor(
        hypervisor_id="hv_test",
        gestor_client=FakeGestorClient(),
        capacity=2,
        lanzador_procesos=FakeLanzador(),
    )
    servicer = HypervisorServicer(hv)
    servidor = await levantar_servidor(
        lambda s: pb_grpc.add_HypervisorServiceServicer_to_server(servicer, s)
    )

    channel = grpc.aio.insecure_channel(servidor.address)
    stub = pb_grpc.HypervisorServiceStub(channel)
    yield stub, hv

    for tarea in hv._watchers.values():
        tarea.cancel()
    await channel.close()


@pytest.mark.integration
async def test_spawn_bot_y_get_bot_stats_via_grpc(cliente_hypervisor):
    stub, _ = cliente_hypervisor
    cfg = common_pb2.BotConfig(bot_id="bot_1", budget=10)

    resp_spawn = await stub.SpawnBot(pb.SpawnBotRequest(config=cfg))
    assert resp_spawn.ok is True

    resp_stats = await stub.GetBotStats(pb.BotIdRequest(bot_id="bot_1"))
    assert resp_stats.points_left == 10


@pytest.mark.integration
async def test_get_bot_stats_bot_desconocido_devuelve_not_found(cliente_hypervisor):
    stub, _ = cliente_hypervisor

    with pytest.raises(grpc.aio.AioRpcError) as exc_info:
        await stub.GetBotStats(pb.BotIdRequest(bot_id="no_existe"))

    assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND


@pytest.mark.integration
async def test_freeze_y_resume_via_grpc(cliente_hypervisor):
    stub, _ = cliente_hypervisor

    resp_freeze = await stub.Freeze(pb.FreezeRequest())
    assert resp_freeze.ok is True

    resp_resume = await stub.Resume(pb.ResumeRequest())
    assert resp_resume.ok is True


@pytest.mark.integration
async def test_reset_budgets_via_grpc_actualiza_puntos_reales(cliente_hypervisor):
    stub, _ = cliente_hypervisor
    await stub.SpawnBot(
        pb.SpawnBotRequest(config=common_pb2.BotConfig(bot_id="bot_1", budget=10))
    )

    resp = await stub.ResetBudgets(
        pb.ResetBudgetsRequest(bot_ids=["bot_1"], default_budget=50, overrides=[])
    )

    assert resp.ok is True
    stats = await stub.GetBotStats(pb.BotIdRequest(bot_id="bot_1"))
    assert stats.points_left == 50


@pytest.mark.integration
async def test_kill_bot_via_grpc(cliente_hypervisor):
    stub, _ = cliente_hypervisor
    await stub.SpawnBot(
        pb.SpawnBotRequest(config=common_pb2.BotConfig(bot_id="bot_1", budget=10))
    )

    resp = await stub.KillBot(pb.BotIdRequest(bot_id="bot_1"))

    assert resp.ok is True
    with pytest.raises(grpc.aio.AioRpcError):
        await stub.GetBotStats(pb.BotIdRequest(bot_id="bot_1"))
