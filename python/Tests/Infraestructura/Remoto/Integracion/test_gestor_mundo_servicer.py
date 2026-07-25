# Tests/Infraestructura/Remoto/Integracion/test_gestor_mundo_servicer.py
"""
test_gestor_mundo_servicer.py — Integración: GestorMundoServicer real
sobre un grpc.aio.server real. GestorMundo se construye SIN llamar a
start() (evitaría abrir canales gRPC reales hacia Gestor_Bots) — se
inyecta manualmente _bots_stub, igual que en los tests unitarios.

Nota de diseño (no bug, pero a vigilar): Pause()/Resume() vía el
servicer asumen que start() ya se llamó (self._bots_stub != None). Si
se invocara Pause antes de start(), gestor_mundo.py lanzaría
AttributeError sin capturar (solo se captura grpc.aio.AioRpcError) —
el propio Funciones/pause.py sí envuelve el handler en un try/except
genérico, así que el RPC no tira el servidor, pero conviene saberlo.
"""

import grpc.aio
import pytest

from Infraestructura.Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo
from Infraestructura.Gestores.Mundo.Gestor_Mundo.gestor_mundo_servicer import (
    GestorMundoServicer,
)
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2 as pb,
    gestor_mundo_service_pb2_grpc as pb_grpc,
)


class FakeBotsStub:
    """Doble mínimo del stub de GestorBotsService — solo lo que
    freeze()/resume() necesitan para no reventar por AttributeError."""

    async def FreezeAll(self, req):
        return common_pb2.Ack(ok=True)

    async def ResumeAll(self, req):
        return common_pb2.Ack(ok=True)


class FakeLogicaClient:
    async def obtener_celdas_en_region(self, *a, **kw):
        return []


@pytest.fixture
async def cliente_gestor_mundo(levantar_servidor):
    gestor = GestorMundo(logica_client=FakeLogicaClient())
    gestor._bots_stub = FakeBotsStub()  # evita depender de start()
    servicer = GestorMundoServicer(gestor)
    servidor = await levantar_servidor(
        lambda s: pb_grpc.add_GestorMundoServiceServicer_to_server(servicer, s)
    )

    channel = grpc.aio.insecure_channel(servidor.address)
    stub = pb_grpc.GestorMundoServiceStub(channel)
    yield stub, gestor
    await channel.close()


@pytest.mark.integration
async def test_heartbeat_ok_sin_sectores_caidos(cliente_gestor_mundo):
    stub, _ = cliente_gestor_mundo
    resp = await stub.Heartbeat(common_pb2.HeartbeatRequest())
    assert resp.ok is True


@pytest.mark.integration
async def test_get_snapshot_info_sin_snapshots_devuelve_ok_false(
    cliente_gestor_mundo, snapshot_dir_aislado
):
    stub, gestor = cliente_gestor_mundo
    gestor.SNAPSHOT_DIR = snapshot_dir_aislado

    resp = await stub.GetSnapshotInfo(pb.GetSnapshotInfoRequest())

    assert resp.ok is False


@pytest.mark.integration
async def test_pause_y_resume_via_grpc(cliente_gestor_mundo):
    stub, gestor = cliente_gestor_mundo

    resp_pause = await stub.Pause(pb.PauseRequest())
    assert resp_pause.ok is True

    resp_resume = await stub.Resume(pb.ResumeRequest())
    assert resp_resume.ok is True


@pytest.mark.integration
async def test_set_tick_rate_via_grpc(cliente_gestor_mundo):
    """Confirma que SetTickRate aplica de verdad el cambio (ver
    CORREGIDO en la cabecera del fichero: antes faltaba el await)."""
    stub, gestor = cliente_gestor_mundo

    resp = await stub.SetTickRate(pb.SetTickRateRequest(ticks_per_second=5))

    assert resp.ok is True
    assert gestor._tick_interval == pytest.approx(0.2)
