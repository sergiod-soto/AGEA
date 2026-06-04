"""
test_sector_unit.py
-------------------
Tests unitarios de Sector, CeldaStore, TickDelta y GestorMundo.
Sin gRPC, sin red, sin AWS.

Carpeta: Tests/Gestor_Mundo/Unit/

Requisitos:
    pip install pytest pytest-asyncio grpcio grpcio-tools

pytest.ini debe contener:
    [pytest]
    asyncio_mode = auto

Ejecutar:
    pytest Tests/Gestor_Mundo/Unit/test_sector_unit.py -v
"""

import asyncio
import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from dataclasses import dataclass
from typing import Any

# ── Ajustar variables de entorno antes de importar los módulos ──────────────
os.environ.update(
    {
        "SECTOR_COL": "1",
        "SECTOR_ROW": "1",
        "SECTOR_SIZE": "10",
        "MAX_VISION_DISTANCE": "3",
        "GRID_WIDTH": "30",
        "GRID_HEIGHT": "30",
        "TICK_TIMEOUT_MS": "500",
        "TICKS_ANTES_DE_DORMIR": "3",
        "SNAPSHOT_DIR": "/tmp/test_snapshots",
        "GESTOR_BOTS_ADDRESS": "localhost:50051",
    }
)

from Gestores.Mundo.Sector.sector import (
    Sector,
    SectorMode,
    CeldaStore,
    TickDelta,
    _ContextoVision,
    REGION_X0,
    REGION_Y0,
    REGION_X1,
    REGION_Y1,
    SECTOR_SIZE,
)
from Gestores.Mundo.Gestor_Mundo.gestor_mundo import (
    GestorMundo,
    SectorInfo,
    SystemState,
    COLS,
    ROWS,
    TICKS_ANTES_DE_DORMIR,
)
from Gestores.Transporte.Proto_Generated.Sectores.sector_service_pb2 import (
    BotSnapshot,
    Position as ProtoPosition,
)

# ═══════════════════════════════════════════════════════════════════════════
#  Fixtures y helpers
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class FakeElementoActivo:
    fuerza_sector_activo: bool = True
    fuerza_vecinos_activos: bool = False
    valor: int = 0


@dataclass
class FakeElementoEstatico:
    fuerza_sector_activo: bool = False
    fuerza_vecinos_activos: bool = False


class FakePosition:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class FakeCell:
    def __init__(self, x, y, element=b"data"):
        self.pos = FakePosition(x, y)
        self.type_id = "FakeElemento"
        self.element = element


class FakeSoundEvent:
    def __init__(self, ox, oy, intensity=50):
        self.origin = FakePosition(ox, oy)
        self.intensity = intensity
        self.payload = b""


def make_bot_proto(bot_id: str, x: int, y: int, budget: int = 100) -> BotSnapshot:
    """Crea un BotSnapshot proto real para usar en tests."""
    return BotSnapshot(
        bot_id=bot_id,
        pos=ProtoPosition(x=x, y=y),
        state=b"",
        budget=budget,
    )


def make_sector() -> Sector:
    s = Sector()
    s._col = 1
    s._row = 1
    s._mode = SectorMode.ACTIVO
    return s


def make_bot_en_centro() -> BotSnapshot:
    cx = REGION_X0 + SECTOR_SIZE // 2
    cy = REGION_Y0 + SECTOR_SIZE // 2
    return make_bot_proto("bot_centro", cx, cy)


def make_bot_en_borde() -> BotSnapshot:
    """Bot justo fuera del borde derecho de la región."""
    return make_bot_proto("bot_borde", REGION_X1, REGION_Y0 + 1)


def make_bot_en_borde_izquierdo() -> BotSnapshot:
    return make_bot_proto("bot_borde_izq", REGION_X0 - 1, REGION_Y0 + 1)


# ═══════════════════════════════════════════════════════════════════════════
#  CeldaStore
# ═══════════════════════════════════════════════════════════════════════════


class TestCeldaStore:

    def test_set_y_get(self):
        store = CeldaStore()
        elem = FakeElementoActivo()
        store.set(5, 5, elem)
        assert store.get(5, 5) is elem

    def test_get_inexistente_devuelve_none(self):
        assert CeldaStore().get(0, 0) is None

    def test_delete_existente(self):
        store = CeldaStore()
        store.set(3, 3, FakeElementoEstatico())
        store.delete(3, 3)
        assert store.get(3, 3) is None

    def test_delete_inexistente_no_lanza(self):
        CeldaStore().delete(99, 99)

    def test_contains(self):
        store = CeldaStore()
        store.set(1, 1, FakeElementoActivo())
        assert (1, 1) in store
        assert (2, 2) not in store

    def test_items_devuelve_todos(self):
        store = CeldaStore()
        store.set(1, 1, FakeElementoActivo())
        store.set(2, 2, FakeElementoEstatico())
        keys = [k for k, _ in store.items()]
        assert (1, 1) in keys
        assert (2, 2) in keys

    def test_from_proto_cell_almacena(self):
        store = CeldaStore()
        cell = FakeCell(5, 7)
        store.from_proto_cell(cell)
        assert store.get(5, 7) is cell

    def test_sobrescribir_celda(self):
        store = CeldaStore()
        store.set(1, 1, FakeElementoActivo(valor=1))
        store.set(1, 1, FakeElementoActivo(valor=2))
        assert store.get(1, 1).valor == 2


# ═══════════════════════════════════════════════════════════════════════════
#  ContextoVision
# ═══════════════════════════════════════════════════════════════════════════


class TestContextoVision:

    def _make_contexto(self):
        store = CeldaStore()
        store.set(REGION_X0 + 1, REGION_Y0 + 1, FakeElementoActivo())
        ghost = {(REGION_X0 - 1, REGION_Y0): FakeElementoEstatico()}
        return _ContextoVision(
            celdas_propias=store,
            ghost=ghost,
            x0=REGION_X0,
            y0=REGION_Y0,
            x1=REGION_X1,
            y1=REGION_Y1,
        )

    def test_get_celda_propia(self):
        ctx = self._make_contexto()
        assert isinstance(
            ctx.get_celda(REGION_X0 + 1, REGION_Y0 + 1), FakeElementoActivo
        )

    def test_get_celda_ghost(self):
        ctx = self._make_contexto()
        assert isinstance(ctx.get_celda(REGION_X0 - 1, REGION_Y0), FakeElementoEstatico)

    def test_get_celda_inexistente(self):
        assert self._make_contexto().get_celda(0, 0) is None

    def test_en_region_propia_dentro(self):
        ctx = self._make_contexto()
        assert ctx.en_region_propia(REGION_X0, REGION_Y0) is True
        assert ctx.en_region_propia(REGION_X1 - 1, REGION_Y1 - 1) is True

    def test_en_region_propia_fuera(self):
        ctx = self._make_contexto()
        assert ctx.en_region_propia(REGION_X1, REGION_Y0) is False
        assert ctx.en_region_propia(REGION_X0 - 1, REGION_Y0) is False

    def test_ghost_no_sobreescribe_propia(self):
        store = CeldaStore()
        propio = FakeElementoActivo(valor=1)
        store.set(REGION_X0, REGION_Y0, propio)
        ghost = {(REGION_X0, REGION_Y0): FakeElementoEstatico()}
        ctx = _ContextoVision(
            celdas_propias=store,
            ghost=ghost,
            x0=REGION_X0,
            y0=REGION_Y0,
            x1=REGION_X1,
            y1=REGION_Y1,
        )
        assert ctx.get_celda(REGION_X0, REGION_Y0).valor == 1


# ═══════════════════════════════════════════════════════════════════════════
#  Sector — ciclo de vida
# ═══════════════════════════════════════════════════════════════════════════


class TestSectorCicloDeVida:

    def test_modo_inicial_inactivo(self):
        assert Sector()._mode == SectorMode.INACTIVO

    def test_set_mode_cambia_modo(self):
        s = make_sector()
        s.set_mode(SectorMode.DORMIDO)
        assert s._mode == SectorMode.DORMIDO

    def test_set_mode_mismo_modo_no_lanza(self):
        s = make_sector()
        s.set_mode(SectorMode.ACTIVO)
        assert s._mode == SectorMode.ACTIVO

    def test_load_state_carga_celdas(self):
        s = make_sector()
        cells = [FakeCell(REGION_X0, REGION_Y0), FakeCell(REGION_X0 + 1, REGION_Y0)]
        s.load_state(cells=cells, bots=[])
        assert s._celdas.get(REGION_X0, REGION_Y0) is not None
        assert s._celdas.get(REGION_X0 + 1, REGION_Y0) is not None

    def test_load_state_carga_bots(self):
        s = make_sector()
        s.load_state(cells=[], bots=[make_bot_en_centro()])
        assert "bot_centro" in s._bots

    def test_load_state_reemplaza_estado_anterior(self):
        s = make_sector()
        s.load_state(cells=[FakeCell(REGION_X0, REGION_Y0)], bots=[])
        s.load_state(cells=[], bots=[])
        assert s._celdas.get(REGION_X0, REGION_Y0) is None

    def test_get_state_devuelve_bots(self):
        s = make_sector()
        s.load_state(cells=[], bots=[make_bot_en_centro()])
        _, bots = s.get_state()
        assert len(bots) == 1


# ═══════════════════════════════════════════════════════════════════════════
#  Sector — FASE 0
# ═══════════════════════════════════════════════════════════════════════════


class TestSectorFase0:

    def test_set_ghost_zone_almacena_celdas(self):
        s = make_sector()
        s.set_ghost_zone(tick_id=1, ghost_cells=[FakeCell(REGION_X0 - 1, REGION_Y0)])
        assert (REGION_X0 - 1, REGION_Y0) in s._ghost

    def test_set_ghost_zone_reemplaza_anterior(self):
        s = make_sector()
        s.set_ghost_zone(tick_id=1, ghost_cells=[FakeCell(REGION_X0 - 1, REGION_Y0)])
        s.set_ghost_zone(tick_id=2, ghost_cells=[FakeCell(REGION_X0 - 2, REGION_Y0)])
        assert (REGION_X0 - 1, REGION_Y0) not in s._ghost
        assert (REGION_X0 - 2, REGION_Y0) in s._ghost

    def test_set_ghost_zone_vacia(self):
        s = make_sector()
        s.set_ghost_zone(tick_id=1, ghost_cells=[FakeCell(REGION_X0 - 1, REGION_Y0)])
        s.set_ghost_zone(tick_id=2, ghost_cells=[])
        assert len(s._ghost) == 0

    def test_set_sounds_almacena(self):
        s = make_sector()
        s.set_sounds(tick_id=1, sounds=[FakeSoundEvent(0, 0), FakeSoundEvent(5, 5)])
        assert len(s._sounds_pendientes) == 2

    def test_set_sounds_reemplaza_anterior(self):
        s = make_sector()
        s.set_sounds(tick_id=1, sounds=[FakeSoundEvent(0, 0)])
        s.set_sounds(tick_id=2, sounds=[FakeSoundEvent(1, 1), FakeSoundEvent(2, 2)])
        assert len(s._sounds_pendientes) == 2

    def test_add_migrating_bot_registra(self):
        s = make_sector()
        s.add_migrating_bot(tick_id=1, bot=make_bot_en_centro())
        assert "bot_centro" in s._bots

    def test_add_migrating_bot_multiples(self):
        s = make_sector()
        s.add_migrating_bot(
            tick_id=1, bot=make_bot_proto("b1", REGION_X0 + 1, REGION_Y0 + 1)
        )
        s.add_migrating_bot(
            tick_id=1, bot=make_bot_proto("b2", REGION_X0 + 2, REGION_Y0 + 2)
        )
        assert len(s._bots) == 2


# ═══════════════════════════════════════════════════════════════════════════
#  Sector — FASE 1: compute_tick
# ═══════════════════════════════════════════════════════════════════════════


class TestSectorComputeTick:

    def test_tick_dormido_devuelve_delta_vacio(self):
        s = make_sector()
        s.set_mode(SectorMode.DORMIDO)
        delta = s.compute_tick(tick_id=1)
        assert delta.tick_id == 1
        assert len(delta.changed_cells) == 0
        assert len(delta.outgoing_bots) == 0
        assert len(delta.dead_bot_ids) == 0

    def test_tick_activo_devuelve_delta(self):
        delta = make_sector().compute_tick(tick_id=1)
        assert isinstance(delta, TickDelta)
        assert delta.tick_id == 1

    def test_tick_actualiza_current_tick_id(self):
        s = make_sector()
        s.compute_tick(tick_id=5)
        assert s._current_tick_id == 5

    def test_tick_limpia_sonidos_pendientes(self):
        s = make_sector()
        s.set_sounds(tick_id=1, sounds=[FakeSoundEvent(0, 0)])
        s.compute_tick(tick_id=1)
        assert len(s._sounds_pendientes) == 0

    def test_tick_guarda_last_delta(self):
        s = make_sector()
        delta = s.compute_tick(tick_id=3)
        assert s._last_delta is delta

    def test_ticks_consecutivos(self):
        s = make_sector()
        for i in range(5):
            delta = s.compute_tick(tick_id=i)
            assert delta.tick_id == i


# ═══════════════════════════════════════════════════════════════════════════
#  Sector — Migraciones
# ═══════════════════════════════════════════════════════════════════════════


class TestSectorMigraciones:

    def test_bot_dentro_no_migra(self):
        s = make_sector()
        s.load_state(cells=[], bots=[make_bot_en_centro()])
        delta = s.compute_tick(tick_id=1)
        assert len(delta.outgoing_bots) == 0
        assert "bot_centro" in s._bots

    def test_bot_fuera_borde_derecho_migra(self):
        s = make_sector()
        s.load_state(cells=[], bots=[make_bot_en_borde()])
        delta = s.compute_tick(tick_id=1)
        assert len(delta.outgoing_bots) == 1
        assert delta.outgoing_bots[0].bot.bot_id == "bot_borde"

    def test_bot_fuera_borde_izquierdo_migra(self):
        s = make_sector()
        s.load_state(cells=[], bots=[make_bot_en_borde_izquierdo()])
        delta = s.compute_tick(tick_id=1)
        assert len(delta.outgoing_bots) == 1

    def test_bot_migrado_se_elimina_del_sector(self):
        s = make_sector()
        s.load_state(cells=[], bots=[make_bot_en_borde()])
        s.compute_tick(tick_id=1)
        assert "bot_borde" not in s._bots

    def test_multiples_bots_solo_migran_los_que_salen(self):
        s = make_sector()
        s.load_state(cells=[], bots=[make_bot_en_centro(), make_bot_en_borde()])
        delta = s.compute_tick(tick_id=1)
        assert len(delta.outgoing_bots) == 1
        assert "bot_centro" in s._bots
        assert "bot_borde" not in s._bots

    def test_bot_en_esquina_exacta_region_no_migra(self):
        s = make_sector()
        s.load_state(
            cells=[], bots=[make_bot_proto("bot_esquina", REGION_X0, REGION_Y0)]
        )
        delta = s.compute_tick(tick_id=1)
        assert len(delta.outgoing_bots) == 0

    def test_bot_en_ultimo_pixel_region_no_migra(self):
        s = make_sector()
        s.load_state(
            cells=[], bots=[make_bot_proto("bot_ultimo", REGION_X1 - 1, REGION_Y1 - 1)]
        )
        delta = s.compute_tick(tick_id=1)
        assert len(delta.outgoing_bots) == 0

    def test_migracion_preserva_budget(self):
        s = make_sector()
        bot = make_bot_proto("bot_borde", REGION_X1, REGION_Y0 + 1, budget=42)
        s.load_state(cells=[], bots=[bot])
        delta = s.compute_tick(tick_id=1)
        assert delta.outgoing_bots[0].bot.budget == 42

    def test_migracion_target_pos_correcta(self):
        s = make_sector()
        s.load_state(cells=[], bots=[make_bot_en_borde()])
        delta = s.compute_tick(tick_id=1)
        tp = delta.outgoing_bots[0].target_pos
        assert tp.x == REGION_X1
        assert tp.y == REGION_Y0 + 1

    def test_migracion_bot_id_preservado(self):
        s = make_sector()
        s.load_state(cells=[], bots=[make_bot_en_borde()])
        delta = s.compute_tick(tick_id=1)
        assert delta.outgoing_bots[0].bot.bot_id == "bot_borde"


# ═══════════════════════════════════════════════════════════════════════════
#  Sector — FASE 2: GetDelta
# ═══════════════════════════════════════════════════════════════════════════


class TestSectorGetDelta:

    def test_get_delta_tick_correcto(self):
        s = make_sector()
        s.compute_tick(tick_id=7)
        assert s.get_delta(tick_id=7) is not None

    def test_get_delta_tick_incorrecto_devuelve_none(self):
        s = make_sector()
        s.compute_tick(tick_id=7)
        assert s.get_delta(tick_id=8) is None

    def test_get_delta_sin_tick_previo_devuelve_none(self):
        assert make_sector().get_delta(tick_id=1) is None

    def test_get_delta_solo_guarda_ultimo_tick(self):
        s = make_sector()
        s.compute_tick(tick_id=1)
        s.compute_tick(tick_id=2)
        assert s.get_delta(tick_id=1) is None
        assert s.get_delta(tick_id=2) is not None


# ═══════════════════════════════════════════════════════════════════════════
#  Sector — Ghost zone
# ═══════════════════════════════════════════════════════════════════════════


class TestSectorGhostZone:

    def test_ghost_zone_accesible_durante_tick(self):
        s = make_sector()
        s.set_ghost_zone(tick_id=1, ghost_cells=[FakeCell(REGION_X0 - 1, REGION_Y0)])
        assert (REGION_X0 - 1, REGION_Y0) in s._ghost

    def test_ghost_zone_no_se_incluye_en_delta(self):
        s = make_sector()
        s.set_ghost_zone(tick_id=1, ghost_cells=[FakeCell(REGION_X0 - 1, REGION_Y0)])
        delta = s.compute_tick(tick_id=1)
        for cell in delta.changed_cells:
            assert not (cell.pos.x == REGION_X0 - 1 and cell.pos.y == REGION_Y0)

    def test_ghost_zone_multiples_celdas(self):
        s = make_sector()
        s.set_ghost_zone(
            tick_id=1,
            ghost_cells=[FakeCell(REGION_X0 - i, REGION_Y0) for i in range(1, 4)],
        )
        assert len(s._ghost) == 3


# ═══════════════════════════════════════════════════════════════════════════
#  GestorMundo — geometría
# ═══════════════════════════════════════════════════════════════════════════


class TestGestorMundoGeometria:

    def _make_gestor(self) -> GestorMundo:
        g = GestorMundo()
        for col in range(COLS):
            for row in range(ROWS):
                info = SectorInfo(
                    col=col,
                    row=row,
                    address=f"localhost:{50100 + col * ROWS + row}",
                    mode=SectorMode.INACTIVO,
                )
                g._sectores[(col, row)] = info
        return g

    def test_sector_para_posicion_correcta(self):
        g = self._make_gestor()
        info = g._sector_para_posicion(SECTOR_SIZE + 1, SECTOR_SIZE + 1)
        assert info is not None
        assert info.col == 1 and info.row == 1

    def test_sector_para_posicion_origen(self):
        g = self._make_gestor()
        info = g._sector_para_posicion(0, 0)
        assert info.col == 0 and info.row == 0

    def test_sector_para_posicion_fuera_del_mapa(self):
        assert self._make_gestor()._sector_para_posicion(9999, 9999) is None

    def test_vecinos_sector_central_tiene_8(self):
        g = self._make_gestor()
        assert len(g._vecinos(g._sectores[(1, 1)])) == 8

    def test_vecinos_sector_esquina_tiene_3(self):
        g = self._make_gestor()
        assert len(g._vecinos(g._sectores[(0, 0)])) == 3

    def test_vecinos_sector_borde_tiene_5(self):
        g = self._make_gestor()
        assert len(g._vecinos(g._sectores[(0, 1)])) == 5

    def test_celdas_de_sector_filtra_correctamente(self):
        g = self._make_gestor()
        g._gold_cells[(SECTOR_SIZE + 1, SECTOR_SIZE + 1)] = b"dentro"
        g._gold_cells[(0, 0)] = b"fuera"
        cells = g._celdas_de_sector(g._sectores[(1, 1)])
        posiciones = [(c.pos.x, c.pos.y) for c in cells]
        assert (SECTOR_SIZE + 1, SECTOR_SIZE + 1) in posiciones
        assert (0, 0) not in posiciones

    def test_ghost_zone_incluye_borde_vecino(self):
        from Gestores.Mundo.Gestor_Mundo.gestor_mundo import MAX_VISION_DISTANCE

        g = self._make_gestor()
        bx, by = SECTOR_SIZE - 1, SECTOR_SIZE - 1
        g._gold_cells[(bx, by)] = b"borde"
        ghost = g._calcular_ghost_zone(g._sectores[(1, 1)])
        assert (bx, by) in [(c.pos.x, c.pos.y) for c in ghost]

    def test_ghost_zone_no_incluye_celdas_propias(self):
        g = self._make_gestor()
        g._gold_cells[(SECTOR_SIZE + 1, SECTOR_SIZE + 1)] = b"propia"
        ghost = g._calcular_ghost_zone(g._sectores[(1, 1)])
        assert (SECTOR_SIZE + 1, SECTOR_SIZE + 1) not in [
            (c.pos.x, c.pos.y) for c in ghost
        ]


# ═══════════════════════════════════════════════════════════════════════════
#  GestorMundo — anti-thrashing
# ═══════════════════════════════════════════════════════════════════════════


class TestGestorMundoAntiThrashing:

    def _make_sector_info(self, col, row, mode) -> SectorInfo:
        info = SectorInfo(col=col, row=row, address="x", mode=mode)
        stub = AsyncMock()
        info.stub = stub
        return info

    async def test_sector_activo_sin_actividad_duerme(self):
        import Gestores.Mundo.Gestor_Mundo.gestor_mundo as gm

        gm.TICKS_ANTES_DE_DORMIR = 3  # forzar el valor que usa el módulo
        g = GestorMundo()
        info = self._make_sector_info(0, 0, SectorMode.ACTIVO)
        info.ticks_sin_actividad = 3
        g._sectores[(0, 0)] = info
        await g._actualizar_modos_sector()
        assert info.mode == SectorMode.DORMIDO
        gm.TICKS_ANTES_DE_DORMIR = 10  # restaurar

    async def test_sector_activo_con_actividad_no_duerme(self):
        import Gestores.Mundo.Gestor_Mundo.gestor_mundo as gm

        gm.TICKS_ANTES_DE_DORMIR = 3
        g = GestorMundo()
        info = self._make_sector_info(0, 0, SectorMode.ACTIVO)
        info.ticks_sin_actividad = 1  # 1+1=2 < 3, no duerme
        g._sectores[(0, 0)] = info
        await g._actualizar_modos_sector()
        assert info.mode == SectorMode.ACTIVO
        gm.TICKS_ANTES_DE_DORMIR = 10

    async def test_vecinos_de_activo_se_despiertan(self):
        import Gestores.Mundo.Gestor_Mundo.gestor_mundo as gm

        gm.TICKS_ANTES_DE_DORMIR = 3
        g = GestorMundo()
        activo = self._make_sector_info(1, 1, SectorMode.ACTIVO)
        activo.ticks_sin_actividad = 0
        vecino = self._make_sector_info(0, 0, SectorMode.INACTIVO)
        g._sectores[(1, 1)] = activo
        g._sectores[(0, 0)] = vecino
        await g._actualizar_modos_sector()
        assert vecino.mode == SectorMode.DORMIDO
        gm.TICKS_ANTES_DE_DORMIR = 10


# ═══════════════════════════════════════════════════════════════════════════
#  GestorMundo — snapshots
# ═══════════════════════════════════════════════════════════════════════════


class TestGestorMundoSnapshots:

    async def test_save_snapshot_crea_fichero(self, tmp_path):
        from Gestores.Mundo.Gestor_Mundo import gestor_mundo as gm_module

        gm_module.SNAPSHOT_DIR = tmp_path
        g = GestorMundo()
        g._tick_id = 42
        await g._save_snapshot()
        assert len(list(tmp_path.glob("mundo_*.json"))) == 1

    async def test_save_snapshot_contenido_correcto(self, tmp_path):
        import json
        from Gestores.Mundo.Gestor_Mundo import gestor_mundo as gm_module

        gm_module.SNAPSHOT_DIR = tmp_path
        g = GestorMundo()
        g._tick_id = 10
        g._gold_cells[(5, 5)] = b"\x01\x02"
        await g._save_snapshot()
        data = json.loads(list(tmp_path.glob("mundo_*.json"))[0].read_text())
        assert data["tick_id"] == 10
        assert "5,5" in data["gold_cells"]

    def test_latest_snapshot_path_sin_snapshots(self, tmp_path):
        from Gestores.Mundo.Gestor_Mundo import gestor_mundo as gm_module

        gm_module.SNAPSHOT_DIR = tmp_path
        assert GestorMundo()._latest_snapshot_path() is None

    async def test_latest_snapshot_path_devuelve_ultimo(self, tmp_path):
        import json
        from Gestores.Mundo.Gestor_Mundo import gestor_mundo as gm_module

        gm_module.SNAPSHOT_DIR = tmp_path
        g = GestorMundo()
        g._tick_id = 1
        await g._save_snapshot()
        g._tick_id = 2
        await g._save_snapshot()
        data = json.loads(g._latest_snapshot_path().read_text())
        assert data["tick_id"] == 2


# ═══════════════════════════════════════════════════════════════════════════
#  GestorMundo — pausa
# ═══════════════════════════════════════════════════════════════════════════


class TestGestorMundoPausa:

    def _make_gestor(self) -> GestorMundo:
        g = GestorMundo()
        g._bots_stub = AsyncMock()
        g._bots_stub.FreezeAll.return_value = MagicMock()
        g._bots_stub.ResumeAll.return_value = MagicMock()
        g._bots_stub.SaveSnapshot.return_value = MagicMock()
        g._pause_event.set()

        info = SectorInfo(col=0, row=0, address="x", mode=SectorMode.ACTIVO)
        stub = AsyncMock()
        stub.SetSectorMode.return_value = MagicMock(ok=True)
        stub.LoadState.return_value = MagicMock(ok=True)
        info.stub = stub
        g._sectores[(0, 0)] = info
        return g

    async def test_freeze_cambia_estado_a_paused(self):
        g = self._make_gestor()
        await g.freeze()
        assert g._state == SystemState.PAUSED

    async def test_freeze_bloquea_pause_event(self):
        g = self._make_gestor()
        await g.freeze()
        assert not g._pause_event.is_set()

    async def test_resume_tras_freeze_reactiva(self):
        g = self._make_gestor()
        await g.freeze()
        await g.resume()
        assert g._state == SystemState.RUNNING
        assert g._pause_event.is_set()

    async def test_freeze_doble_no_lanza(self):
        g = self._make_gestor()
        await g.freeze()
        await g.freeze()
        assert g._state == SystemState.PAUSED

    async def test_resume_sin_freeze_no_lanza(self):
        g = self._make_gestor()
        await g.resume()
        assert g._state == SystemState.RUNNING

    async def test_freeze_llama_a_gestor_bots(self):
        g = self._make_gestor()
        await g.freeze()
        g._bots_stub.FreezeAll.assert_called_once()

    async def test_resume_llama_a_gestor_bots(self):
        g = self._make_gestor()
        await g.freeze()
        await g.resume()
        g._bots_stub.ResumeAll.assert_called_once()
