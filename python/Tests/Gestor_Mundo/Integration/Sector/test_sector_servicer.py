"""
Integration/Sector/test_sector_servicer.py
Tests de integración del SectorServicer con un Sector real (sin red gRPC).
Verifica que el dispatch del servicer conecta correctamente con la lógica del sector.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from Tests.conftest import make_mock_cell, make_mock_bot


@pytest.fixture
def servicer(sector):
    from Infraestructura.Gestores.Mundo.Sector.sector_servicer import SectorServicer
    from Infraestructura.Gestores.Mundo.Sector.registry import FUNCIONES

    with patch("Infraestructura.Gestores.Mundo.Sector.sector_servicer.FUNCIONES", FUNCIONES):
        return SectorServicer(sector)


@pytest.fixture
def context():
    ctx = AsyncMock()
    ctx.abort = AsyncMock()
    return ctx


# ---------------------------------------------------------------------------
# SetSectorMode
# ---------------------------------------------------------------------------


class TestSetSectorMode:
    async def test_set_modo_activo(self, servicer, context):
        from Infraestructura.Gestores.Mundo.Sector.sector import SectorMode

        request = MagicMock()
        request.mode = SectorMode.ACTIVO.value
        resp = await servicer.SetSectorMode(request, context)
        assert resp.ok is True
        assert servicer._sector._mode == SectorMode.ACTIVO

    async def test_set_modo_invalido(self, servicer, context):
        request = MagicMock()
        request.mode = 999
        resp = await servicer.SetSectorMode(request, context)
        assert resp.ok is False
        assert resp.error != ""


# ---------------------------------------------------------------------------
# LoadState / GetState
# ---------------------------------------------------------------------------


class TestLoadGetState:
    async def test_load_y_get_state(self, servicer, context):
        from Infraestructura.Gestores.Transporte.Proto_Generated.common_pb2 import (
            Cell,
            Position,
            BotSnapshot,
        )

        cells = [
            Cell(pos=Position(x=1, y=1), element=b"data"),
            Cell(pos=Position(x=2, y=2), element=b"data"),
        ]
        bots = [BotSnapshot(bot_id="bot_001", pos=Position(x=1, y=1), budget=100)]

        load_req = MagicMock()
        load_req.cells = cells
        load_req.bots = bots
        load_resp = await servicer.LoadState(load_req, context)
        assert load_resp.ok is True

        get_req = MagicMock()
        get_resp = await servicer.GetState(get_req, context)
        assert get_resp.ok is True

    async def test_load_estado_vacio(self, servicer, context):
        request = MagicMock()
        request.cells = []
        request.bots = []
        resp = await servicer.LoadState(request, context)
        assert resp.ok is True


# ---------------------------------------------------------------------------
# SetGhostZone / SetSounds / AddMigratingBot (FASE 0)
# ---------------------------------------------------------------------------


class TestFase0:
    async def test_set_ghost_zone(self, servicer, context):
        request = MagicMock()
        request.tick_id = 1
        request.ghost_cells = [make_mock_cell(10, 10)]
        resp = await servicer.SetGhostZone(request, context)
        assert resp.ok is True
        assert (10, 10) in servicer._sector._ghost

    @pytest.mark.skip(reason="SetSounds pendiente de implementar")
    async def test_set_sounds(self, servicer, context):
        request = MagicMock()
        request.tick_id = 1
        request.sounds = [MagicMock(), MagicMock()]
        resp = await servicer.SetSounds(request, context)
        assert resp.ok is True
        assert len(servicer._sector._sounds_pendientes) == 2

    async def test_add_migrating_bot(self, servicer, context):
        request = MagicMock()
        request.tick_id = 1
        request.bot = make_mock_bot("bot_migrante", 5, 5)
        resp = await servicer.AddMigratingBot(request, context)
        assert resp.ok is True
        assert "bot_migrante" in servicer._sector._bots

    async def test_fase0_lock_serializa_operaciones(self, servicer, context):
        """SetGhostZone y SetSounds no se ejecutan simultáneamente."""
        results = []

        async def ghost():
            req = MagicMock()
            req.tick_id = 1
            req.ghost_cells = []
            await servicer.SetGhostZone(req, context)
            results.append("ghost")

        async def sounds():
            req = MagicMock()
            req.tick_id = 1
            req.sounds = []
            await servicer.SetSounds(req, context)
            results.append("sounds")

        await asyncio.gather(ghost(), sounds())
        assert set(results) == {"ghost", "sounds"}


# ---------------------------------------------------------------------------
# StartTick / GetDelta
# ---------------------------------------------------------------------------


class TestStartGetTick:
    async def test_start_tick_sector_inactivo(self, servicer, context):
        request = MagicMock()
        request.tick_id = 1
        request.timeout_ms = 1000
        resp = await servicer.StartTick(request, context)
        assert resp.ok is True

    async def test_start_y_get_delta(self, servicer, context):
        from Infraestructura.Gestores.Mundo.Sector.sector import SectorMode

        servicer._sector.set_mode(SectorMode.ACTIVO)

        start_req = MagicMock()
        start_req.tick_id = 5
        start_req.timeout_ms = 1000
        start_resp = await servicer.StartTick(start_req, context)
        assert start_resp.ok is True

        get_req = MagicMock()
        get_req.tick_id = 5
        get_resp = await servicer.GetDelta(get_req, context)
        assert get_resp.ok is True
        assert get_resp.tick_id == 5

    async def test_get_delta_tick_incorrecto(self, servicer, context):
        from Infraestructura.Gestores.Mundo.Sector.sector import SectorMode

        servicer._sector.set_mode(SectorMode.ACTIVO)

        start_req = MagicMock()
        start_req.tick_id = 5
        start_req.timeout_ms = 1000
        await servicer.StartTick(start_req, context)

        get_req = MagicMock()
        get_req.tick_id = 99
        get_resp = await servicer.GetDelta(get_req, context)
        assert get_resp.ok is False

    async def test_start_tick_timeout(self, servicer, context):
        from Infraestructura.Gestores.Mundo.Sector.sector import SectorMode, TickDelta

        servicer._sector.set_mode(SectorMode.ACTIVO)

        def tick_lento(tick_id):
            import time

            time.sleep(10)
            return TickDelta(tick_id=tick_id)

        with patch.object(servicer._sector, "compute_tick", side_effect=tick_lento):
            request = MagicMock()
            request.tick_id = 1
            request.timeout_ms = 1  # 1ms — debe expirar
            resp = await servicer.StartTick(request, context)
            assert resp.timed_out is True


# ---------------------------------------------------------------------------
# SaveSnapshot
# ---------------------------------------------------------------------------


class TestSaveSnapshot:
    async def test_save_snapshot(self, servicer, context):
        request = MagicMock()
        request.snapshot_id = "snap_001"
        with patch.object(
            servicer._sector, "save_snapshot", new_callable=AsyncMock
        ) as mock_save:
            mock_save.return_value = None
            resp = await servicer.SaveSnapshot(request, context)
        assert resp.ok is True
        assert resp.snapshot_id == "snap_001"
        mock_save.assert_called_once_with(snapshot_id="snap_001")


# ---------------------------------------------------------------------------
# Flujo completo FASE 0 → 1 → 2
# ---------------------------------------------------------------------------


class TestFlujoCompleto:
    async def test_ciclo_completo_un_tick(self, servicer, context):
        from Infraestructura.Gestores.Mundo.Sector.sector import SectorMode

        servicer._sector.set_mode(SectorMode.ACTIVO)

        # FASE 0
        ghost_req = MagicMock()
        ghost_req.tick_id = 1
        ghost_req.ghost_cells = []
        await servicer.SetGhostZone(ghost_req, context)

        sounds_req = MagicMock()
        sounds_req.tick_id = 1
        sounds_req.sounds = []
        await servicer.SetSounds(sounds_req, context)

        # FASE 1
        start_req = MagicMock()
        start_req.tick_id = 1
        start_req.timeout_ms = 1000
        start_resp = await servicer.StartTick(start_req, context)
        assert start_resp.ok is True
        assert start_resp.timed_out is False

        # FASE 2
        delta_req = MagicMock()
        delta_req.tick_id = 1
        delta_resp = await servicer.GetDelta(delta_req, context)
        assert delta_resp.ok is True
        assert delta_resp.tick_id == 1
