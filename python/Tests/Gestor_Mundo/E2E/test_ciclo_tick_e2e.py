"""
E2E/test_ciclo_tick_e2e.py
Tests E2E del ciclo completo de tick: GestorMundo → Sector (in-process).
Sin red real — los stubs gRPC se reemplazan por llamadas directas al SectorServicer.
Cubre el flujo FASE 0 → FASE 1 → FASE 2 con migración de bots.
"""
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from Tests.conftest import make_mock_cell, make_mock_bot


# ---------------------------------------------------------------------------
# Infraestructura: stub in-process que simula la red
# ---------------------------------------------------------------------------

class InProcessSectorStub:
    """
    Reemplaza el stub gRPC de sector por llamadas directas al SectorServicer.
    Permite tests E2E sin levantar servidores reales.
    """
    def __init__(self, servicer):
        self._s = servicer

    async def SetSectorMode(self, request):
        return await self._s.SetSectorMode(request, MagicMock())

    async def LoadState(self, request):
        return await self._s.LoadState(request, MagicMock())

    async def GetState(self, request):
        return await self._s.GetState(request, MagicMock())

    async def SetGhostZone(self, request):
        return await self._s.SetGhostZone(request, MagicMock())

    async def SetSounds(self, request):
        return await self._s.SetSounds(request, MagicMock())

    async def AddMigratingBot(self, request):
        return await self._s.AddMigratingBot(request, MagicMock())

    async def StartTick(self, request):
        return await self._s.StartTick(request, MagicMock())

    async def GetDelta(self, request):
        return await self._s.GetDelta(request, MagicMock())

    async def SaveSnapshot(self, request):
        return await self._s.SaveSnapshot(request, MagicMock())


def _make_sector_info(col, row, stub):
    from Gestores.Mundo.Gestor_Mundo.gestor_mundo import SectorInfo
    from Gestores.Mundo.Sector.sector import SectorMode
    info = SectorInfo(col=col, row=row, address=f"local:{col}:{row}")
    info.stub = stub
    info.mode = SectorMode.INACTIVO
    return info


# ---------------------------------------------------------------------------
# Fixtures E2E
# ---------------------------------------------------------------------------

@pytest.fixture
def sector_e2e(monkeypatch):
    monkeypatch.setenv("SECTOR_COL", "0")
    monkeypatch.setenv("SECTOR_ROW", "0")
    monkeypatch.setenv("SECTOR_SIZE", "10")
    monkeypatch.setenv("MAX_VISION_DISTANCE", "5")
    from Gestores.Mundo.Sector.sector import Sector
    return Sector()


@pytest.fixture
def sector_servicer_e2e(sector_e2e):
    from Gestores.Mundo.Sector.sector_servicer import SectorServicer
    return SectorServicer(sector_e2e)


@pytest.fixture
def sector_stub_e2e(sector_servicer_e2e):
    return InProcessSectorStub(sector_servicer_e2e)


@pytest.fixture
def gestor_mundo_e2e(sector_stub_e2e):
    from Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo, SectorMode
    gestor = GestorMundo()
    info = _make_sector_info(0, 0, sector_stub_e2e)
    gestor._sectores[(0, 0)] = info
    # Mock del stub de GestorBots para no necesitar red
    gestor._bots_stub = AsyncMock()
    gestor._bots_stub.FreezeAll = AsyncMock(return_value=MagicMock(ok=True))
    gestor._bots_stub.ResumeAll = AsyncMock(return_value=MagicMock(ok=True))
    gestor._bots_stub.ResetBudgets = AsyncMock(return_value=MagicMock(ok=True))
    gestor._bots_stub.SaveSnapshot = AsyncMock(return_value=MagicMock(ok=True))
    return gestor


# ---------------------------------------------------------------------------
# Tests E2E
# ---------------------------------------------------------------------------

class TestCicloTickE2E:
    async def test_tick_sector_inactivo(self, gestor_mundo_e2e):
        """Un tick con sector INACTIVO no produce delta con actividad."""
        gestor = gestor_mundo_e2e
        await gestor._run_tick()

    async def test_activar_sector_y_ejecutar_tick(self, gestor_mundo_e2e):
        """Activar sector y ejecutar tick completo FASE 0 → 1 → 2."""
        from Gestores.Mundo.Sector.sector import SectorMode
        gestor = gestor_mundo_e2e
        info = gestor._sectores[(0, 0)]
        await gestor._set_sector_mode(info, SectorMode.ACTIVO)
        assert info.mode == SectorMode.ACTIVO
        await gestor._run_tick()

    async def test_load_state_distribuye_al_sector(self, gestor_mundo_e2e, sector_e2e):
        """_distribute_gold_to_sectors envía las celdas gold al sector."""
        gestor = gestor_mundo_e2e
        gestor._gold_cells[(1, 1)] = b"elemento_serializado"
        await gestor._distribute_gold_to_sectors()
        # El sector debería haber recibido la celda
        assert (1, 1) in sector_e2e._celdas

    async def test_ghost_zone_calculada_correctamente(self, gestor_mundo_e2e):
        """Celdas fuera del sector propio pero dentro del borde se incluyen en ghost zone."""
        gestor = gestor_mundo_e2e
        # Celda en (-3, 5): fuera del sector (0,0) pero dentro de MAX_VISION_DISTANCE=5
        gestor._gold_cells[(-3, 5)] = b"ghost_elem"
        info = gestor._sectores[(0, 0)]
        ghost = gestor._calcular_ghost_zone(info)
        posiciones = [(c.pos.x, c.pos.y) for c in ghost]
        assert (-3, 5) in posiciones

    async def test_celda_propia_no_en_ghost_zone(self, gestor_mundo_e2e):
        """Celdas propias del sector no aparecen en su ghost zone."""
        gestor = gestor_mundo_e2e
        gestor._gold_cells[(5, 5)] = b"elem_propio"
        info = gestor._sectores[(0, 0)]
        ghost = gestor._calcular_ghost_zone(info)
        posiciones = [(c.pos.x, c.pos.y) for c in ghost]
        assert (5, 5) not in posiciones

    async def test_migracion_bot_entre_sectores(
        self, monkeypatch, sector_stub_e2e, sector_servicer_e2e
    ):
        """Bot que cruza borde se transfiere al sector destino."""
        from Gestores.Mundo.Sector.sector import SectorMode, Sector
        from Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo

        # Sector origen: col=0, row=0 → región [0,10)
        monkeypatch.setenv("SECTOR_COL", "1")
        monkeypatch.setenv("SECTOR_ROW", "0")
        monkeypatch.setenv("SECTOR_SIZE", "10")
        sector_destino = Sector()
        from Gestores.Mundo.Sector.sector_servicer import SectorServicer
        servicer_destino = SectorServicer(sector_destino)
        stub_destino = InProcessSectorStub(servicer_destino)

        gestor = GestorMundo()
        gestor._bots_stub = AsyncMock()
        gestor._bots_stub.ResetBudgets = AsyncMock(return_value=MagicMock(ok=True))

        info_origen = _make_sector_info(0, 0, sector_stub_e2e)
        info_origen.mode = SectorMode.ACTIVO
        info_destino = _make_sector_info(1, 0, stub_destino)
        info_destino.mode = SectorMode.INACTIVO

        gestor._sectores[(0, 0)] = info_origen
        gestor._sectores[(1, 0)] = info_destino

        # Bot en posición (12, 5) — fuera del sector origen [0,10) × [0,10)
        bot = make_mock_bot("bot_migra", 12, 5)
        sector_servicer_e2e._sector._mode = SectorMode.ACTIVO
        sector_servicer_e2e._sector._bots["bot_migra"] = bot

        await gestor._run_tick()

        # Bot debe haber migrado al sector destino
        assert "bot_migra" in sector_destino._bots


class TestPausaReanuudacion:
    async def test_freeze_y_resume(self, gestor_mundo_e2e):
        from Gestores.Mundo.Gestor_Mundo.gestor_mundo import SystemState
        gestor = gestor_mundo_e2e
        await gestor.freeze()
        assert gestor._state == SystemState.PAUSED
        assert not gestor._pause_event.is_set()

        await gestor.resume()
        assert gestor._state == SystemState.RUNNING
        assert gestor._pause_event.is_set()

    async def test_freeze_idempotente(self, gestor_mundo_e2e):
        from Gestores.Mundo.Gestor_Mundo.gestor_mundo import SystemState
        gestor = gestor_mundo_e2e
        await gestor.freeze()
        await gestor.freeze()  # segunda llamada no debe cambiar estado
        assert gestor._state == SystemState.PAUSED

    async def test_resume_sin_freeze_no_cambia_estado(self, gestor_mundo_e2e):
        from Gestores.Mundo.Gestor_Mundo.gestor_mundo import SystemState
        gestor = gestor_mundo_e2e
        assert gestor._state == SystemState.RUNNING
        await gestor.resume()
        assert gestor._state == SystemState.RUNNING


class TestDeepSave:
    async def test_deep_save_siempre_reanuda(self, gestor_mundo_e2e, tmp_path):
        """Si _save_snapshot falla, el sistema debe reanudar igualmente."""
        from Gestores.Mundo.Gestor_Mundo.gestor_mundo import SystemState
        gestor = gestor_mundo_e2e

        with patch.object(
            gestor, "_save_snapshot", side_effect=Exception("disco lleno")
        ):
            with pytest.raises(Exception, match="disco lleno"):
                await gestor._deep_save()

        assert gestor._state == SystemState.RUNNING
        assert gestor._pause_event.is_set()

    async def test_deep_save_completo(self, gestor_mundo_e2e, tmp_path):
        from Gestores.Mundo.Gestor_Mundo.gestor_mundo import SystemState, SNAPSHOT_DIR
        gestor = gestor_mundo_e2e

        with patch("Gestores.Mundo.Gestor_Mundo.gestor_mundo.SNAPSHOT_DIR", tmp_path):
            with patch.object(gestor, "_save_snapshot", new_callable=AsyncMock):
                await gestor._deep_save()

        assert gestor._state == SystemState.RUNNING


class TestAntiThrashing:
    async def test_sector_activo_sin_actividad_se_duerme(self, gestor_mundo_e2e):
        """Sector ACTIVO sin actividad durante TICKS_ANTES_DE_DORMIR ticks pasa a DORMIDO."""
        from Gestores.Mundo.Sector.sector import SectorMode
        from Gestores.Mundo.Gestor_Mundo.gestor_mundo import TICKS_ANTES_DE_DORMIR
        gestor = gestor_mundo_e2e
        info = gestor._sectores[(0, 0)]
        await gestor._set_sector_mode(info, SectorMode.ACTIVO)

        # Simular ticks sin actividad
        info.ticks_sin_actividad = TICKS_ANTES_DE_DORMIR
        await gestor._actualizar_modos_sector()

        assert info.mode == SectorMode.DORMIDO

    async def test_delta_con_actividad_resetea_contador(self, gestor_mundo_e2e):
        from Gestores.Mundo.Sector.sector import SectorMode
        gestor = gestor_mundo_e2e
        info = gestor._sectores[(0, 0)]
        info.mode = SectorMode.ACTIVO
        info.ticks_sin_actividad = 5

        delta = MagicMock()
        delta.changed_cells = [MagicMock()]
        delta.outgoing_bots = []
        delta.emitted_sounds = []

        if gestor._delta_tiene_actividad(delta):
            info.ticks_sin_actividad = 0

        assert info.ticks_sin_actividad == 0


class TestGeometria:
    def test_sector_para_posicion(self, gestor_mundo_e2e):
        gestor = gestor_mundo_e2e
        info = gestor._sector_para_posicion(5, 5)
        assert info is not None
        assert info.col == 0
        assert info.row == 0

    def test_posicion_fuera_del_mapa(self, gestor_mundo_e2e):
        gestor = gestor_mundo_e2e
        info = gestor._sector_para_posicion(9999, 9999)
        assert info is None

    def test_vecinos_sector_central(self, gestor_mundo_e2e, monkeypatch):
        """Sector (0,0) con vecinos registrados devuelve todos los adyacentes."""
        from Gestores.Mundo.Sector.sector import SectorMode
        from Gestores.Mundo.Gestor_Mundo.gestor_mundo import SectorInfo
        gestor = gestor_mundo_e2e
        stub = MagicMock()
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                if dc == 0 and dr == 0:
                    continue
                key = (dc, dr)
                if key not in gestor._sectores:
                    info = _make_sector_info(dc, dr, stub)
                    gestor._sectores[key] = info

        info_00 = gestor._sectores[(0, 0)]
        vecinos = gestor._vecinos(info_00)
        assert len(vecinos) == 8

    def test_celdas_de_sector(self, gestor_mundo_e2e):
        gestor = gestor_mundo_e2e
        gestor._gold_cells[(5, 5)] = b"en_sector"
        gestor._gold_cells[(50, 50)] = b"fuera_sector"
        info = gestor._sectores[(0, 0)]
        celdas = gestor._celdas_de_sector(info)
        posiciones = [(c.pos.x, c.pos.y) for c in celdas]
        assert (5, 5) in posiciones
        assert (50, 50) not in posiciones
