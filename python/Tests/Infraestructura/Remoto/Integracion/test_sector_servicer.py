# Tests/Infraestructura/Remoto/Integracion/test_sector_servicer.py
"""
test_sector_servicer.py — Integración: SectorServicer real sobre un
grpc.aio.server real (puerto efímero, ver fixture levantar_servidor de
conftest.py), golpeado con un stub gRPC real — valida serialización
proto + dispatch, no solo la lógica en memoria de Sector (ya cubierta
en Tests/Infraestructura/Remoto/Unitarios/test_sector.py).
"""

import grpc.aio
import pytest

from Infraestructura.Gestores.Mundo.Sector.sector import Sector, SectorMode
from Infraestructura.Gestores.Mundo.Sector.sector_servicer import SectorServicer
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    sector_service_pb2 as pb,
    sector_service_pb2_grpc as pb_grpc,
)


@pytest.fixture
async def cliente_sector(levantar_servidor, monkeypatch):
    """
    Instancia un Sector real (col=0,row=0,size=100) tras el servicer,
    y devuelve (stub, sector) para poder comprobar tanto la respuesta
    gRPC como el estado interno resultante.
    """
    monkeypatch.setenv("SECTOR_COL", "0")
    monkeypatch.setenv("SECTOR_ROW", "0")
    monkeypatch.setenv("SECTOR_SIZE", "100")

    sector = Sector()
    servicer = SectorServicer(sector)
    servidor = await levantar_servidor(
        lambda s: pb_grpc.add_SectorServiceServicer_to_server(servicer, s)
    )

    channel = grpc.aio.insecure_channel(servidor.address)
    stub = pb_grpc.SectorServiceStub(channel)
    yield stub, sector
    await channel.close()


@pytest.mark.integration
async def test_set_sector_mode_via_grpc_cambia_estado_real(cliente_sector):
    stub, sector = cliente_sector

    resp = await stub.SetSectorMode(
        pb.SetSectorModeRequest(mode=pb.SectorMode.Value("ACTIVO"))
    )

    assert resp.ok is True
    assert sector._mode == SectorMode.ACTIVO


@pytest.mark.integration
async def test_load_state_y_get_state_roundtrip_via_grpc(cliente_sector):
    stub, _ = cliente_sector
    cell = common_pb2.Cell(pos=common_pb2.Position(x=5, y=5))
    bot = common_pb2.BotSnapshot(
        bot_id="bot_1", pos=common_pb2.Position(x=5, y=5), budget=10
    )

    resp_load = await stub.LoadState(pb.LoadStateRequest(cells=[cell], bots=[bot]))
    assert resp_load.ok is True

    resp_state = await stub.GetState(pb.GetStateRequest())
    assert resp_state.ok is True
    assert len(resp_state.cells) == 1
    assert resp_state.bots[0].bot_id == "bot_1"


@pytest.mark.integration
async def test_start_tick_y_get_delta_mismo_tick_id(cliente_sector):
    stub, sector = cliente_sector
    sector.set_mode(SectorMode.ACTIVO)

    resp_tick = await stub.StartTick(pb.StartTickRequest(tick_id=1, timeout_ms=500))
    assert resp_tick.ok is True
    assert resp_tick.timed_out is False

    resp_delta = await stub.GetDelta(pb.GetDeltaRequest(tick_id=1))
    assert resp_delta.ok is True
    assert resp_delta.tick_id == 1


@pytest.mark.integration
async def test_get_delta_con_tick_id_distinto_falla(cliente_sector):
    stub, sector = cliente_sector
    sector.set_mode(SectorMode.ACTIVO)
    await stub.StartTick(pb.StartTickRequest(tick_id=1, timeout_ms=500))

    resp_delta = await stub.GetDelta(pb.GetDeltaRequest(tick_id=99))

    assert resp_delta.ok is False


@pytest.mark.integration
async def test_set_ghost_zone_via_grpc(cliente_sector):
    stub, sector = cliente_sector
    cell = common_pb2.Cell(pos=common_pb2.Position(x=50, y=50))

    resp = await stub.SetGhostZone(
        pb.SetGhostZoneRequest(tick_id=1, ghost_cells=[cell])
    )

    assert resp.ok is True
    assert (50, 50) in sector._ghost


@pytest.mark.integration
async def test_set_sounds_via_grpc(cliente_sector):
    stub, _ = cliente_sector

    resp = await stub.SetSounds(pb.SetSoundsRequest(tick_id=1, sounds=[]))

    assert resp.ok is True


@pytest.mark.integration
async def test_save_snapshot_via_grpc(cliente_sector):
    stub, _ = cliente_sector

    resp = await stub.SaveSnapshot(pb.SaveSnapshotRequest(snapshot_id="snap_1"))

    assert resp.ok is True
    assert resp.snapshot_id == "snap_1"


@pytest.mark.integration
async def test_add_migrating_bot_via_grpc(cliente_sector):
    stub, sector = cliente_sector
    bot = common_pb2.BotSnapshot(
        bot_id="bot_migrado", pos=common_pb2.Position(x=10, y=10), budget=5
    )

    resp = await stub.AddMigratingBot(pb.AddMigratingBotRequest(tick_id=1, bot=bot))

    assert resp.ok is True
    assert "bot_migrado" in sector._bots
