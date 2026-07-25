# Tests/Infraestructura/Remoto/Integracion/test_world_proxy_servicer_grpc.py
"""
test_world_proxy_servicer_grpc.py — Confirma que Act() queda
correctamente enlazado al RPC real declarado en
world_proxy_service.proto, sobre un grpc.server SÍNCRONO real (el HV
no usa grpc.aio — mismo patrón que test_hypervisor_servicer.py).

Antes de la corrección, Act() no existía (el framework habría
devuelto UNIMPLEMENTED) y Rotar()/Interact() nunca eran alcanzables
porque no estaban en el .proto. Este fichero es la prueba end-to-end
de que ese hueco ya no existe.
"""

from concurrent import futures

import grpc
import pytest

from Infraestructura.Gestores.Bots.Hypervisor.hypervisor import Hypervisor
from Infraestructura.Gestores.Bots.Hypervisor.world_proxy_servicer import (
    WorldProxyServicer,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    world_proxy_service_pb2 as pb,
    world_proxy_service_pb2_grpc as pb_grpc,
)
from Infraestructura.Gestores.tipos_comunes import ActionResult


@pytest.fixture
def levantar_servidor_sincrono():
    """Mismo patrón que en test_hypervisor_servicer.py — el HV corre
    sobre grpc.server (síncrono), no grpc.aio.server."""
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
    def wait(self):
        import threading

        threading.Event().wait()


class FakeLanzador:
    def lanzar(self, hypervisor_id, bot_id, codigo_gz, env_extra):
        return FakeProceso()

    def limpiar(self, hypervisor_id, bot_id):
        pass


class FakeGestorClient:
    def forward_action(self, bot_id, hypervisor_id, action_type, payload):
        return ActionResult(ok=True, payload=b"ok_gestor", error="", world_tick=1)

    def notificar_avatar_sin_piloto(self, bot_id):
        pass


@pytest.fixture
def cliente_world_proxy(levantar_servidor_sincrono):
    hv = Hypervisor(
        hypervisor_id="hv_test",
        gestor_client=FakeGestorClient(),
        capacity=5,
        lanzador_procesos=FakeLanzador(),
    )
    hv.spawn_bot({"bot_id": "bot_1", "budget": 10})
    servicer = WorldProxyServicer(hv)
    address = levantar_servidor_sincrono(
        lambda s: pb_grpc.add_WorldProxyServiceServicer_to_server(servicer, s)
    )

    channel = grpc.insecure_channel(address)
    stub = pb_grpc.WorldProxyServiceStub(channel)
    yield stub
    channel.close()


@pytest.mark.integration
def test_act_via_grpc_real_reenvia_al_gestor(cliente_world_proxy):
    resp = cliente_world_proxy.Act(
        pb.ActRequest(action_name="mover", payload=b"payload"),
        metadata=(("bot-id", "bot_1"),),
    )

    assert resp.ok is True
    assert resp.payload == b"ok_gestor"


@pytest.mark.integration
def test_act_via_grpc_sin_bot_id_header_rechaza(cliente_world_proxy):
    with pytest.raises(grpc.RpcError) as exc_info:
        cliente_world_proxy.Act(pb.ActRequest(action_name="mover", payload=b""))

    assert exc_info.value.code() == grpc.StatusCode.UNAUTHENTICATED