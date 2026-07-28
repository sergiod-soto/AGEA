# Tests/Infraestructura/Remoto/Unitarios/test_logica_mundo.py
"""
test_logica_mundo.py — Pruebas unitarias de LogicaMundo: crear/
modificar/eliminar elemento, eliminar_avatar_bot, snapshot roundtrip,
y el tick_actual que usa Vista_Foco (ver comunicaciones_remoto.py /
vista_foco.py) para detectar "hubo tick nuevo".

Se usa un elemento mínimo real (Agua, ya definido en el proyecto y sin
dependencias de comportamientos complejos) en vez de un mock, porque
crear_elemento() pasa por reconstruir_elemento() (registry.py) — un
mock no ejercitaría la ruta de (de)serialización real, que es
justamente lo que más interesa comprobar aquí.
"""

import json

from numpy import uint64
import pytest

from Infraestructura.Gestores.Mundo.Logica_Mundo.logica_mundo import LogicaMundo


def _elemento_agua_bytes(eid: int) -> bytes:
    """
    Construye el blob serializado mínimo que crear_elemento() espera:
    un dict con '__clase__' (usado por registry.reconstruir_elemento)
    y 'id' (leído por LogicaMundo._slot_bytes_a_id).
    """
    return json.dumps(
        {
            "__clase__": "Agua",
            "id": eid,
            "comportamientos": {},
        }
    ).encode()


@pytest.fixture
def logica() -> LogicaMundo:
    # gestor_bots_client=None es válido — solo lo usa matar_bot(), que
    # no se ejercita en estos tests.
    return LogicaMundo(gestor_bots_client=None)


@pytest.mark.unit
async def test_crear_elemento_suelo_ok(logica: LogicaMundo):
    ok, error = await logica.crear_elemento(
        pos=(3, 4), type_id="suelo", element=_elemento_agua_bytes(eid=1)
    )
    assert ok is True
    assert error == ""
    assert (3, 4) in logica._gold_cells
    assert logica._gold_cells[(3, 4)].suelo == 1


@pytest.mark.unit
async def test_crear_elemento_bot_registra_bot_positions(logica: LogicaMundo):
    ok, _ = await logica.crear_elemento(
        pos=(5, 5), type_id="bot", element=_elemento_agua_bytes(eid=42)
    )
    assert ok is True
    assert logica._bot_positions["42"] == (5, 5)


@pytest.mark.unit
async def test_crear_elemento_sin_id_falla(logica: LogicaMundo):
    blob = json.dumps({"__clase__": "Agua", "comportamientos": {}}).encode()
    ok, error = await logica.crear_elemento(pos=(0, 0), type_id="suelo", element=blob)
    assert ok is False
    assert "id" in error.lower()


@pytest.mark.unit
async def test_eliminar_elemento_vacia_celda_si_queda_sin_slots(logica: LogicaMundo):
    await logica.crear_elemento(
        pos=(1, 1), type_id="suelo", element=_elemento_agua_bytes(1)
    )
    ok, _ = await logica.eliminar_elemento(pos=(1, 1), element_id=uint64(1))
    assert ok is True
    assert (1, 1) not in logica._gold_cells, "la celda debe desaparecer si queda vacía"


@pytest.mark.unit
async def test_eliminar_elemento_desconocido_falla(logica: LogicaMundo):
    await logica.crear_elemento(
        pos=(2, 2), type_id="suelo", element=_elemento_agua_bytes(1)
    )
    ok, error = await logica.eliminar_elemento(pos=(2, 2), element_id=uint64(999))
    assert ok is False
    assert "no encontrado" in error.lower()


@pytest.mark.unit
async def test_eliminar_avatar_bot_limpia_bot_positions(logica: LogicaMundo):
    await logica.crear_elemento(
        pos=(7, 7), type_id="bot", element=_elemento_agua_bytes(10)
    )
    ok, _ = await logica.eliminar_avatar_bot(bot_id="10")
    assert ok is True
    assert "10" not in logica._bot_positions


@pytest.mark.unit
async def test_eliminar_avatar_bot_desconocido_falla(logica: LogicaMundo):
    ok, error = await logica.eliminar_avatar_bot(bot_id="no_existe")
    assert ok is False
    assert "no encontrado" in error.lower()


@pytest.mark.unit
async def test_save_y_load_snapshot_roundtrip(
    logica: LogicaMundo, snapshot_dir_aislado
):
    """
    snapshot_dir_aislado (de conftest.py) redirige SNAPSHOT_DIR a
    tmp_path — importante releer logica.SNAPSHOT_DIR después de aplicar
    el monkeypatch, ya que LogicaMundo lo lee en __init__ (antes de que
    la fixture entre en efecto si no se pide como dependencia primero).
    """
    logica.SNAPSHOT_DIR = snapshot_dir_aislado

    await logica.crear_elemento(
        pos=(9, 9), type_id="suelo", element=_elemento_agua_bytes(99)
    )
    await logica.save_snapshot("test_snap")

    logica2 = LogicaMundo(gestor_bots_client=None)
    logica2.SNAPSHOT_DIR = snapshot_dir_aislado
    await logica2.load_state("test_snap")

    assert (9, 9) in logica2._gold_cells
    assert logica2._gold_cells[(9, 9)].suelo == 99
    assert 99 in logica2._elements


@pytest.mark.unit
async def test_load_state_snapshot_inexistente_no_lanza(
    logica: LogicaMundo, snapshot_dir_aislado
):
    logica.SNAPSHOT_DIR = snapshot_dir_aislado
    await logica.load_state("no_existe_este_id")  # no debe lanzar, solo loguear warning
    assert logica._gold_cells == {}


# ── tick_actual — NUEVO, lo necesita Vista_Foco (FocoBroadcaster) ──


@pytest.mark.unit
async def test_get_tick_actual_es_cero_antes_de_cualquier_avance(logica: LogicaMundo):
    """
    Estado inicial: nadie ha llamado a avanzar_elementos_globales
    todavía — FocoBroadcaster debe poder distinguir esto de un tick
    real ya procesado.
    """
    assert await logica.get_tick_actual() == 0


@pytest.mark.unit
async def test_avanzar_elementos_globales_guarda_el_tick_recibido(logica: LogicaMundo):
    await logica.avanzar_elementos_globales(tick_id=5)

    assert await logica.get_tick_actual() == 5


@pytest.mark.unit
async def test_avanzar_elementos_globales_repetido_actualiza_el_tick(
    logica: LogicaMundo,
):
    """
    No es un contador que solo suma: guarda el ÚLTIMO tick_id recibido,
    tal cual, incluso si se llama varias veces seguidas.
    """
    await logica.avanzar_elementos_globales(tick_id=5)
    await logica.avanzar_elementos_globales(tick_id=8)

    assert await logica.get_tick_actual() == 8
