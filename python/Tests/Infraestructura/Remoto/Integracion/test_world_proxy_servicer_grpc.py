# Tests/Infraestructura/Remoto/Integracion/test_world_proxy_servicer_grpc.py
"""
test_world_proxy_servicer_grpc.py — Confirma que Act() queda
correctamente enlazado al RPC real declarado en
world_proxy_service.proto.

ADAPTADO tras la migración de Hypervisor a asyncio (ver docstring de
hypervisor.py): antes este fichero usaba su propia fixture con un
grpc.server SÍNCRONO (el HV no usaba grpc.aio) — ahora que
WorldProxyServicer/Hypervisor son async de punta a punta, se usa la
`levantar_servidor` compartida de conftest.py (grpc.aio real), igual
que el resto de servicers async del proyecto, y el stub/las llamadas
pasan a ser async.

Antes de la corrección original (no relacionada con esta migración),
Act() no existía (el framework habría devuelto UNIMPLEMENTED) y
Rotar()/Interact() nunca eran alcanzables porque no estaban en el
.proto. Este fichero sigue siendo la prueba end-to-end de que ese
hueco no existe.
"""

import asyncio

import grpc.aio
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


class FakeProceso:
    """Proceso que nunca termina por sí solo. wait() async — ver
    mismo patrón en test_hypervisor.py: bloquear con threading.Event
    aquí congelaría el loop de eventos del servidor."""

    async def wait(self):
        await asyncio.Event().wait()

    def terminate(self):
        pass


class FakeLanzador:
    async def lanzar(self, hypervisor_id, bot_id, codigo_gz, env_extra):
        return FakeProceso()

    def limpiar(self, hypervisor_id, bot_id):
        pass


class FakeGestorClient:
    """
    forward_action async: Hypervisor.forward_to_gestor ahora hace
    `await self.gestor_client.forward_action(...)`.
    """

    async def forward_action(self, bot_id, hypervisor_id, action_type, payload):
        return ActionResult(ok=True, payload=b"ok_gestor", error="", world_tick=1)

    async def notificar_avatar_sin_piloto(self, bot_id):
        pass


@pytest.fixture
async def cliente_world_proxy(levantar_servidor):
    hv = Hypervisor(
        hypervisor_id="hv_test",
        gestor_client=FakeGestorClient(),
        capacity=5,
        lanzador_procesos=FakeLanzador(),
    )
    await hv.spawn_bot({"bot_id": "bot_1", "budget": 10})
    servicer = WorldProxyServicer(hv)
    servidor = await levantar_servidor(
        lambda s: pb_grpc.add_WorldProxyServiceServicer_to_server(servicer, s)
    )

    channel = grpc.aio.insecure_channel(servidor.address)
    stub = pb_grpc.WorldProxyServiceStub(channel)
    yield stub

    for tarea in hv._watchers.values():
        tarea.cancel()
    await channel.close()


@pytest.mark.integration
async def test_act_via_grpc_real_reenvia_al_gestor(cliente_world_proxy):
    resp = await cliente_world_proxy.Act(
        pb.ActRequest(action_name="mover", payload=b"payload"),
        metadata=(("bot-id", "bot_1"),),
    )

    assert resp.ok is True
    assert resp.payload == b"ok_gestor"


@pytest.mark.integration
async def test_act_via_grpc_sin_bot_id_header_rechaza(cliente_world_proxy):
    with pytest.raises(grpc.aio.AioRpcError) as exc_info:
        await cliente_world_proxy.Act(pb.ActRequest(action_name="mover", payload=b""))

    assert exc_info.value.code() == grpc.StatusCode.UNAUTHENTICATED
