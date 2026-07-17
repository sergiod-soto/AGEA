# Tests/Infraestructura/Remoto/Unitarios/test_sector.py
"""
test_sector.py — Pruebas unitarias de Sector (Gestores/Mundo/Sector/
sector.py). Hasta ahora la clase solo se usaba como FakeStub dentro de
los tests de GestorMundo — su propia lógica interna (detección de
migraciones, ghost zone, get_delta con tick_id desincronizado) nunca
se había ejercitado directamente.

Se construyen Cell/BotSnapshot con los tipos protobuf REALES (no
dobles) porque _detectar_migraciones() los empaqueta como campos
tipados de un mensaje protobuf (MigratingBot(bot=..., ...)) — protobuf
valida el tipo en tiempo de asignación, así que un doble Python
cualquiera haría fallar la construcción del mensaje, no el test en sí.
"""

import pytest

from Infraestructura.Gestores.Mundo.Sector.sector import Sector, SectorMode
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2


@pytest.fixture
def sector_test(monkeypatch) -> Sector:
    """
    Sector col=0,row=0,size=100 → región propia = [0,100) x [0,100).
    Las variables de entorno se fijan ANTES de instanciar Sector(),
    que las lee en su __init__ (ver docstring de la clase: "siempre
    leer del entorno vivo para que los tests puedan sobreescribirlas").
    """
    monkeypatch.setenv("SECTOR_COL", "0")
    monkeypatch.setenv("SECTOR_ROW", "0")
    monkeypatch.setenv("SECTOR_SIZE", "100")
    return Sector()


def _bot(bot_id: str, x: int, y: int, budget: int = 10) -> common_pb2.BotSnapshot:
    return common_pb2.BotSnapshot(
        bot_id=bot_id, pos=common_pb2.Position(x=x, y=y), budget=budget
    )


def _cell(x: int, y: int) -> common_pb2.Cell:
    return common_pb2.Cell(pos=common_pb2.Position(x=x, y=y))


# ── load_state / get_state ──────────────────────────────────────


@pytest.mark.unit
def test_load_state_carga_celdas_y_bots_indexados_por_posicion(sector_test):
    sector_test.load_state(cells=[_cell(5, 5)], bots=[_bot("b1", 5, 5)])

    assert (5, 5) in sector_test._celdas
    assert "b1" in sector_test._bots


@pytest.mark.unit
def test_get_state_devuelve_lo_cargado_en_load_state(sector_test):
    sector_test.load_state(cells=[_cell(1, 1)], bots=[_bot("b1", 1, 1)])

    cells, bots = sector_test.get_state()

    assert len(cells) == 1
    assert (cells[0].pos.x, cells[0].pos.y) == (1, 1)
    assert bots[0].bot_id == "b1"


# ── set_mode ─────────────────────────────────────────────────────


@pytest.mark.unit
def test_set_mode_al_mismo_valor_no_lanza(sector_test):
    sector_test.set_mode(SectorMode.INACTIVO)  # ya es el modo inicial
    assert sector_test._mode == SectorMode.INACTIVO


# ── FASE 0 ───────────────────────────────────────────────────────


@pytest.mark.unit
def test_set_ghost_zone_indexa_celdas_por_posicion(sector_test):
    sector_test.set_ghost_zone(tick_id=1, ghost_cells=[_cell(200, 200)])
    assert (200, 200) in sector_test._ghost


@pytest.mark.unit
def test_set_sounds_almacena_pendientes(sector_test):
    sector_test.set_sounds(tick_id=1, sounds=["sonido_falso"])
    assert sector_test._sounds_pendientes == ["sonido_falso"]


@pytest.mark.unit
def test_add_migrating_bot_registra_en_bots(sector_test):
    sector_test.add_migrating_bot(tick_id=1, bot=_bot("b_nuevo", 10, 10))
    assert "b_nuevo" in sector_test._bots


# ── compute_tick / migraciones ───────────────────────────────────


@pytest.mark.unit
def test_compute_tick_en_modo_inactivo_devuelve_delta_vacio(sector_test):
    sector_test._bots["b1"] = _bot("b1", 500, 500)  # fuera de la región

    delta = sector_test.compute_tick(tick_id=1)

    assert delta.outgoing_bots == []
    assert "b1" in sector_test._bots  # en INACTIVO no se procesa nada


@pytest.mark.unit
def test_compute_tick_detecta_bot_que_migro_fuera_de_la_region(sector_test):
    sector_test.set_mode(SectorMode.ACTIVO)
    sector_test._bots["b1"] = _bot("b1", 150, 5)  # x=150 fuera de [0,100)

    delta = sector_test.compute_tick(tick_id=1)

    assert len(delta.outgoing_bots) == 1
    assert delta.outgoing_bots[0].bot.bot_id == "b1"
    assert delta.outgoing_bots[0].target_pos.x == 150
    assert "b1" not in sector_test._bots  # se retira del sector de origen


@pytest.mark.unit
def test_compute_tick_bot_dentro_de_la_region_no_migra(sector_test):
    sector_test.set_mode(SectorMode.ACTIVO)
    sector_test._bots["b1"] = _bot("b1", 50, 50)

    delta = sector_test.compute_tick(tick_id=1)

    assert delta.outgoing_bots == []
    assert "b1" in sector_test._bots


# ── get_delta ────────────────────────────────────────────────────


@pytest.mark.unit
def test_get_delta_devuelve_none_si_tick_id_no_coincide(sector_test):
    sector_test.set_mode(SectorMode.ACTIVO)
    sector_test.compute_tick(tick_id=1)

    assert sector_test.get_delta(tick_id=2) is None


@pytest.mark.unit
def test_get_delta_devuelve_el_delta_del_tick_solicitado(sector_test):
    sector_test.set_mode(SectorMode.ACTIVO)
    delta_generado = sector_test.compute_tick(tick_id=7)

    assert sector_test.get_delta(tick_id=7) is delta_generado
