"""
test_sector_servicer_integration.py
------------------------------------
Tests de integración del SectorServicer.

Levanta un servidor gRPC real en puerto aleatorio y ejercita todos los
métodos del SectorService con un cliente gRPC real. Sin mocks de red.

Carpeta destino: Tests/Gestor_Mundo/Integration/

Requisitos:
    pip install pytest pytest-asyncio grpcio grpcio-tools

pytest.ini (o pyproject.toml) debe contener:
    [pytest]
    asyncio_mode = auto

Ejecutar desde D:/AGEA/python/:
    pytest Tests/Gestor_Mundo/Integration/test_sector_servicer_integration.py -v
"""

import os
import pytest
import grpc

from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import sector_service_pb2 as pb

# ── Variables de entorno ANTES de cualquier import del proyecto ─────────────
# SECTOR_COL=1, SECTOR_ROW=1, SECTOR_SIZE=10
# → REGION_X0=10, REGION_Y0=10, REGION_X1=20, REGION_Y1=20
os.environ.update(
    {
        "SECTOR_COL": "1",
        "SECTOR_ROW": "1",
        "SECTOR_SIZE": "10",
        "MAX_VISION_DISTANCE": "3",
    }
)

from Infraestructura.Gestores.Mundo.Sector.sector import Sector, SectorMode
from Infraestructura.Gestores.Mundo.Sector.sector_servicer import SectorServicer
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    sector_service_pb2_grpc as pb_grpc,
)

# Constantes de región derivadas del entorno (col=1, row=1, size=10)
REGION_X0 = 10
REGION_Y0 = 10
REGION_X1 = 20
REGION_Y1 = 20


# ═══════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════


def _make_bot(bot_id: str, x: int, y: int, budget: int = 100) -> pb.BotSnapshot:
    return pb.BotSnapshot(
        bot_id=bot_id,
        pos=pb.Position(x=x, y=y),
        state=b"",
        budget=budget,
    )


def _make_cell(x: int, y: int, element: bytes = b"\x01") -> pb.Cell:
    return pb.Cell(pos=pb.Position(x=x, y=y), element=element)


def _bot_dentro(bot_id: str = "bot_dentro") -> pb.BotSnapshot:
    """Bot en el centro de la región (col=1,row=1,size=10 → [10,20))."""
    return _make_bot(bot_id, x=15, y=15)


def _bot_fuera(bot_id: str = "bot_fuera") -> pb.BotSnapshot:
    """Bot justo en el borde derecho (x=REGION_X1 → fuera)."""
    return _make_bot(bot_id, x=REGION_X1, y=REGION_Y0 + 1)


# ═══════════════════════════════════════════════════════════════════════════
#  Fixture: servidor gRPC real en puerto aleatorio
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
async def sector_server():
    """
    Levanta SectorServicer en un puerto aleatorio.
    Yield: (stub, sector_obj) — stub gRPC ya conectado + referencia al Sector.
    """
    sector = Sector()
    servicer = SectorServicer(sector)

    server = grpc.aio.server()
    pb_grpc.add_SectorServiceServicer_to_server(servicer, server)
    port = server.add_insecure_port("[::]:0")  # puerto aleatorio
    await server.start()

    channel = grpc.aio.insecure_channel(f"localhost:{port}")
    stub = pb_grpc.SectorServiceStub(channel)

    yield stub, sector

    await channel.close()
    await server.stop(grace=0)


# ═══════════════════════════════════════════════════════════════════════════
#  SetSectorMode
# ═══════════════════════════════════════════════════════════════════════════


class TestSetSectorMode:

    async def test_set_mode_activo_ok(self, sector_server):
        stub, sector = sector_server
        resp = await stub.SetSectorMode(
            pb.SetSectorModeRequest(mode=pb.SectorMode.ACTIVO)
        )
        assert resp.ok is True
        assert sector._mode == SectorMode.ACTIVO

    async def test_set_mode_dormido_ok(self, sector_server):
        stub, sector = sector_server
        resp = await stub.SetSectorMode(
            pb.SetSectorModeRequest(mode=pb.SectorMode.DORMIDO)
        )
        assert resp.ok is True
        assert sector._mode == SectorMode.DORMIDO

    async def test_set_mode_inactivo_ok(self, sector_server):
        stub, sector = sector_server
        # Primero activar, luego volver a INACTIVO
        await stub.SetSectorMode(pb.SetSectorModeRequest(mode=pb.SectorMode.ACTIVO))
        resp = await stub.SetSectorMode(
            pb.SetSectorModeRequest(mode=pb.SectorMode.INACTIVO)
        )
        assert resp.ok is True
        assert sector._mode == SectorMode.INACTIVO

    async def test_set_mode_mismo_modo_no_error(self, sector_server):
        stub, _ = sector_server
        await stub.SetSectorMode(pb.SetSectorModeRequest(mode=pb.SectorMode.ACTIVO))
        resp = await stub.SetSectorMode(
            pb.SetSectorModeRequest(mode=pb.SectorMode.ACTIVO)
        )
        assert resp.ok is True


# ═══════════════════════════════════════════════════════════════════════════
#  LoadState / GetState
# ═══════════════════════════════════════════════════════════════════════════


class TestLoadStateGetState:

    async def test_load_state_vacio_ok(self, sector_server):
        stub, _ = sector_server
        resp = await stub.LoadState(pb.LoadStateRequest(cells=[], bots=[]))
        assert resp.ok is True

    async def test_load_state_con_celdas(self, sector_server):
        stub, sector = sector_server
        cells = [_make_cell(REGION_X0, REGION_Y0), _make_cell(REGION_X0 + 1, REGION_Y0)]
        resp = await stub.LoadState(pb.LoadStateRequest(cells=cells, bots=[]))
        assert resp.ok is True
        assert sector._celdas.get(REGION_X0, REGION_Y0) is not None

    async def test_load_state_con_bots(self, sector_server):
        stub, sector = sector_server
        resp = await stub.LoadState(pb.LoadStateRequest(cells=[], bots=[_bot_dentro()]))
        assert resp.ok is True
        assert "bot_dentro" in sector._bots

    async def test_get_state_devuelve_bots_cargados(self, sector_server):
        stub, _ = sector_server
        await stub.LoadState(
            pb.LoadStateRequest(
                cells=[], bots=[_bot_dentro("bot_A"), _bot_dentro("bot_B")]
            )
        )
        resp = await stub.GetState(pb.GetStateRequest())
        assert resp.ok is True
        ids = {b.bot_id for b in resp.bots}
        assert {"bot_A", "bot_B"} == ids

    async def test_load_state_reemplaza_estado_anterior(self, sector_server):
        stub, sector = sector_server
        await stub.LoadState(
            pb.LoadStateRequest(cells=[], bots=[_bot_dentro("bot_viejo")])
        )
        await stub.LoadState(pb.LoadStateRequest(cells=[], bots=[]))
        assert "bot_viejo" not in sector._bots

    async def test_get_state_sin_load_devuelve_vacio(self, sector_server):
        stub, _ = sector_server
        resp = await stub.GetState(pb.GetStateRequest())
        assert resp.ok is True
        assert len(resp.bots) == 0


# ═══════════════════════════════════════════════════════════════════════════
#  FASE 0 — SetGhostZone / SetSounds / AddMigratingBot
# ═══════════════════════════════════════════════════════════════════════════


class TestFase0:

    async def test_set_ghost_zone_ok(self, sector_server):
        stub, sector = sector_server
        ghost_cells = [_make_cell(REGION_X0 - 1, REGION_Y0)]
        resp = await stub.SetGhostZone(
            pb.SetGhostZoneRequest(tick_id=1, ghost_cells=ghost_cells)
        )
        assert resp.ok is True
        assert (REGION_X0 - 1, REGION_Y0) in sector._ghost

    async def test_set_ghost_zone_reemplaza_anterior(self, sector_server):
        stub, sector = sector_server
        await stub.SetGhostZone(
            pb.SetGhostZoneRequest(
                tick_id=1, ghost_cells=[_make_cell(REGION_X0 - 1, REGION_Y0)]
            )
        )
        await stub.SetGhostZone(
            pb.SetGhostZoneRequest(
                tick_id=2, ghost_cells=[_make_cell(REGION_X0 - 2, REGION_Y0)]
            )
        )
        assert (REGION_X0 - 1, REGION_Y0) not in sector._ghost
        assert (REGION_X0 - 2, REGION_Y0) in sector._ghost

    # async def test_set_sounds_ok(self, sector_server):
    #     stub, sector = sector_server
    #     sounds = [
    #         pb.SoundEvent(
    #             origin=pb.Position(x=0, y=0), intensity=50, payload=b""
    #         )
    #     ]
    #     resp = await stub.SetSounds(pb.SetSoundsRequest(tick_id=1, sounds=sounds))
    #     assert resp.ok is True
    #     assert len(sector._sounds_pendientes) == 1

    # async def test_set_sounds_vacio_ok(self, sector_server):
    #     stub, sector = sector_server
    #     resp = await stub.SetSounds(pb.SetSoundsRequest(tick_id=1, sounds=[]))
    #     assert resp.ok is True
    #     assert len(sector._sounds_pendientes) == 0

    async def test_add_migrating_bot_registra(self, sector_server):
        stub, sector = sector_server
        resp = await stub.AddMigratingBot(
            pb.AddMigratingBotRequest(tick_id=1, bot=_bot_dentro("bot_migrado"))
        )
        assert resp.ok is True
        assert "bot_migrado" in sector._bots

    async def test_add_migrating_bot_multiples(self, sector_server):
        stub, sector = sector_server
        for i in range(3):
            await stub.AddMigratingBot(
                pb.AddMigratingBotRequest(
                    tick_id=1, bot=_make_bot(f"bot_{i}", x=15, y=15)
                )
            )
        assert len(sector._bots) == 3


# ═══════════════════════════════════════════════════════════════════════════
#  FASE 1 — StartTick
# ═══════════════════════════════════════════════════════════════════════════


class TestStartTick:

    async def test_start_tick_sector_activo_ok(self, sector_server):
        stub, _ = sector_server
        await stub.SetSectorMode(pb.SetSectorModeRequest(mode=pb.SectorMode.ACTIVO))
        resp = await stub.StartTick(pb.StartTickRequest(tick_id=1, timeout_ms=5000))
        assert resp.ok is True
        assert resp.timed_out is False

    async def test_start_tick_sector_dormido_ok(self, sector_server):
        stub, _ = sector_server
        await stub.SetSectorMode(pb.SetSectorModeRequest(mode=pb.SectorMode.DORMIDO))
        resp = await stub.StartTick(pb.StartTickRequest(tick_id=1, timeout_ms=5000))
        assert resp.ok is True

    async def test_start_tick_actualiza_current_tick_id(self, sector_server):
        stub, sector = sector_server
        await stub.SetSectorMode(pb.SetSectorModeRequest(mode=pb.SectorMode.ACTIVO))
        await stub.StartTick(pb.StartTickRequest(tick_id=7, timeout_ms=5000))
        assert sector._current_tick_id == 7

    async def test_start_tick_limpia_sonidos(self, sector_server):
        stub, sector = sector_server
        await stub.SetSectorMode(pb.SetSectorModeRequest(mode=pb.SectorMode.ACTIVO))
        sounds = [
            pb.SoundEvent(origin=pb.Position(x=0, y=0), intensity=10, payload=b"")
        ]
        await stub.SetSounds(pb.SetSoundsRequest(tick_id=1, sounds=sounds))
        await stub.StartTick(pb.StartTickRequest(tick_id=1, timeout_ms=5000))
        assert len(sector._sounds_pendientes) == 0

    async def test_start_tick_consecutivos(self, sector_server):
        stub, sector = sector_server
        await stub.SetSectorMode(pb.SetSectorModeRequest(mode=pb.SectorMode.ACTIVO))
        for i in range(5):
            resp = await stub.StartTick(pb.StartTickRequest(tick_id=i, timeout_ms=5000))
            assert resp.ok is True
        assert sector._current_tick_id == 4


# ═══════════════════════════════════════════════════════════════════════════
#  FASE 2 — GetDelta
# ═══════════════════════════════════════════════════════════════════════════


class TestGetDelta:

    async def test_get_delta_tick_correcto(self, sector_server):
        stub, _ = sector_server
        await stub.SetSectorMode(pb.SetSectorModeRequest(mode=pb.SectorMode.ACTIVO))
        await stub.StartTick(pb.StartTickRequest(tick_id=3, timeout_ms=5000))
        resp = await stub.GetDelta(pb.GetDeltaRequest(tick_id=3))
        assert resp.ok is True
        assert resp.tick_id == 3

    async def test_get_delta_tick_incorrecto_devuelve_error(self, sector_server):
        stub, _ = sector_server
        await stub.SetSectorMode(pb.SetSectorModeRequest(mode=pb.SectorMode.ACTIVO))
        await stub.StartTick(pb.StartTickRequest(tick_id=3, timeout_ms=5000))
        resp = await stub.GetDelta(pb.GetDeltaRequest(tick_id=99))
        assert resp.ok is False
        assert resp.error != ""

    async def test_get_delta_sin_tick_previo_error(self, sector_server):
        stub, _ = sector_server
        resp = await stub.GetDelta(pb.GetDeltaRequest(tick_id=1))
        assert resp.ok is False

    async def test_get_delta_sector_dormido_delta_vacio(self, sector_server):
        stub, _ = sector_server
        await stub.SetSectorMode(pb.SetSectorModeRequest(mode=pb.SectorMode.DORMIDO))
        await stub.StartTick(pb.StartTickRequest(tick_id=1, timeout_ms=5000))
        resp = await stub.GetDelta(pb.GetDeltaRequest(tick_id=1))
        assert resp.ok is True
        assert len(resp.outgoing_bots) == 0
        assert len(resp.changed_cells) == 0

    async def test_get_delta_solo_guarda_ultimo_tick(self, sector_server):
        stub, _ = sector_server
        await stub.SetSectorMode(pb.SetSectorModeRequest(mode=pb.SectorMode.ACTIVO))
        await stub.StartTick(pb.StartTickRequest(tick_id=1, timeout_ms=5000))
        await stub.StartTick(pb.StartTickRequest(tick_id=2, timeout_ms=5000))
        resp_viejo = await stub.GetDelta(pb.GetDeltaRequest(tick_id=1))
        resp_nuevo = await stub.GetDelta(pb.GetDeltaRequest(tick_id=2))
        assert resp_viejo.ok is False
        assert resp_nuevo.ok is True


# ═══════════════════════════════════════════════════════════════════════════
#  Ciclo completo FASE 0 → FASE 1 → FASE 2
# ═══════════════════════════════════════════════════════════════════════════


class TestCicloCompleto:

    async def test_ciclo_sin_bots(self, sector_server):
        """LoadState → SetGhostZone → SetSounds → StartTick → GetDelta."""
        stub, _ = sector_server
        await stub.SetSectorMode(pb.SetSectorModeRequest(mode=pb.SectorMode.ACTIVO))
        await stub.LoadState(pb.LoadStateRequest(cells=[], bots=[]))

        # FASE 0
        await stub.SetGhostZone(
            pb.SetGhostZoneRequest(
                tick_id=1,
                ghost_cells=[_make_cell(REGION_X0 - 1, REGION_Y0)],
            )
        )
        await stub.SetSounds(pb.SetSoundsRequest(tick_id=1, sounds=[]))

        # FASE 1
        tick_resp = await stub.StartTick(
            pb.StartTickRequest(tick_id=1, timeout_ms=5000)
        )
        assert tick_resp.ok is True

        # FASE 2
        delta_resp = await stub.GetDelta(pb.GetDeltaRequest(tick_id=1))
        assert delta_resp.ok is True
        assert delta_resp.tick_id == 1

    async def test_ciclo_bot_que_no_migra(self, sector_server):
        """Bot dentro de la región → no aparece en outgoing_bots."""
        stub, _ = sector_server
        await stub.SetSectorMode(pb.SetSectorModeRequest(mode=pb.SectorMode.ACTIVO))
        await stub.LoadState(pb.LoadStateRequest(cells=[], bots=[_bot_dentro()]))
        await stub.SetGhostZone(pb.SetGhostZoneRequest(tick_id=1, ghost_cells=[]))
        await stub.SetSounds(pb.SetSoundsRequest(tick_id=1, sounds=[]))
        await stub.StartTick(pb.StartTickRequest(tick_id=1, timeout_ms=5000))

        delta_resp = await stub.GetDelta(pb.GetDeltaRequest(tick_id=1))
        assert delta_resp.ok is True
        assert len(delta_resp.outgoing_bots) == 0

    async def test_ciclo_bot_que_migra(self, sector_server):
        """Bot fuera de la región → aparece en outgoing_bots."""
        stub, _ = sector_server
        await stub.SetSectorMode(pb.SetSectorModeRequest(mode=pb.SectorMode.ACTIVO))
        await stub.LoadState(pb.LoadStateRequest(cells=[], bots=[_bot_fuera()]))
        await stub.SetGhostZone(pb.SetGhostZoneRequest(tick_id=1, ghost_cells=[]))
        await stub.SetSounds(pb.SetSoundsRequest(tick_id=1, sounds=[]))
        await stub.StartTick(pb.StartTickRequest(tick_id=1, timeout_ms=5000))

        delta_resp = await stub.GetDelta(pb.GetDeltaRequest(tick_id=1))
        assert delta_resp.ok is True
        assert len(delta_resp.outgoing_bots) == 1
        assert delta_resp.outgoing_bots[0].bot.bot_id == "bot_fuera"

    async def test_ciclo_bot_migrado_via_add_migrating_bot(self, sector_server):
        """
        Simula lo que haría Gestor_Mundo: añade un bot via AddMigratingBot,
        hace tick, verifica que si está dentro no migra.
        """
        stub, _ = sector_server
        await stub.SetSectorMode(pb.SetSectorModeRequest(mode=pb.SectorMode.ACTIVO))
        await stub.LoadState(pb.LoadStateRequest(cells=[], bots=[]))

        # FASE 0: bot llega por migración
        await stub.AddMigratingBot(
            pb.AddMigratingBotRequest(
                tick_id=1, bot=_make_bot("bot_recien_llegado", x=15, y=15)
            )
        )
        await stub.SetGhostZone(pb.SetGhostZoneRequest(tick_id=1, ghost_cells=[]))
        await stub.SetSounds(pb.SetSoundsRequest(tick_id=1, sounds=[]))

        # FASE 1
        await stub.StartTick(pb.StartTickRequest(tick_id=1, timeout_ms=5000))

        # FASE 2
        delta_resp = await stub.GetDelta(pb.GetDeltaRequest(tick_id=1))
        assert delta_resp.ok is True
        assert len(delta_resp.outgoing_bots) == 0  # está dentro, no migra

    async def test_ciclo_multiples_ticks(self, sector_server):
        """Tres ticks consecutivos, cada uno coherente."""
        stub, _ = sector_server
        await stub.SetSectorMode(pb.SetSectorModeRequest(mode=pb.SectorMode.ACTIVO))
        await stub.LoadState(pb.LoadStateRequest(cells=[], bots=[]))

        for tick_id in range(1, 4):
            await stub.SetGhostZone(
                pb.SetGhostZoneRequest(tick_id=tick_id, ghost_cells=[])
            )
            await stub.SetSounds(pb.SetSoundsRequest(tick_id=tick_id, sounds=[]))
            t_resp = await stub.StartTick(
                pb.StartTickRequest(tick_id=tick_id, timeout_ms=5000)
            )
            assert t_resp.ok is True

            d_resp = await stub.GetDelta(pb.GetDeltaRequest(tick_id=tick_id))
            assert d_resp.ok is True
            assert d_resp.tick_id == tick_id

    async def test_ciclo_migracion_preserva_budget(self, sector_server):
        """El budget del bot se conserva en outgoing_bots."""
        stub, _ = sector_server
        await stub.SetSectorMode(pb.SetSectorModeRequest(mode=pb.SectorMode.ACTIVO))
        bot = _make_bot("bot_rico", x=REGION_X1, y=REGION_Y0 + 1, budget=777)
        await stub.LoadState(pb.LoadStateRequest(cells=[], bots=[bot]))
        await stub.SetGhostZone(pb.SetGhostZoneRequest(tick_id=1, ghost_cells=[]))
        await stub.SetSounds(pb.SetSoundsRequest(tick_id=1, sounds=[]))
        await stub.StartTick(pb.StartTickRequest(tick_id=1, timeout_ms=5000))

        delta_resp = await stub.GetDelta(pb.GetDeltaRequest(tick_id=1))
        assert delta_resp.outgoing_bots[0].bot.budget == 777


# ═══════════════════════════════════════════════════════════════════════════
#  SaveSnapshot
# ═══════════════════════════════════════════════════════════════════════════


class TestSaveSnapshot:

    async def test_save_snapshot_ok(self, sector_server):
        stub, _ = sector_server
        resp = await stub.SaveSnapshot(pb.SaveSnapshotRequest(snapshot_id="snap_001"))
        assert resp.ok is True
        assert resp.snapshot_id == "snap_001"

    async def test_save_snapshot_id_preservado(self, sector_server):
        stub, _ = sector_server
        sid = "snap_xyz_42"
        resp = await stub.SaveSnapshot(pb.SaveSnapshotRequest(snapshot_id=sid))
        assert resp.snapshot_id == sid

    async def test_save_snapshot_multiples_ok(self, sector_server):
        stub, _ = sector_server
        for i in range(3):
            resp = await stub.SaveSnapshot(
                pb.SaveSnapshotRequest(snapshot_id=f"snap_{i:03d}")
            )
            assert resp.ok is True

    async def test_save_snapshot_con_estado(self, sector_server):
        """SaveSnapshot funciona aunque haya celdas y bots cargados."""
        stub, _ = sector_server
        await stub.SetSectorMode(pb.SetSectorModeRequest(mode=pb.SectorMode.ACTIVO))
        await stub.LoadState(
            pb.LoadStateRequest(
                cells=[_make_cell(REGION_X0, REGION_Y0)],
                bots=[_bot_dentro()],
            )
        )
        await stub.StartTick(pb.StartTickRequest(tick_id=1, timeout_ms=5000))
        resp = await stub.SaveSnapshot(pb.SaveSnapshotRequest(snapshot_id="snap_final"))
        assert resp.ok is True
