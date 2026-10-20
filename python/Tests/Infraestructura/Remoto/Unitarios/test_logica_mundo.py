# Tests/Infraestructura/Remoto/Unitarios/test_logica_mundo.py
"""
test_logica_mundo.py — Pruebas unitarias de LogicaMundo: crear/
modificar/eliminar elemento, eliminar_avatar_bot, matar_bot, snapshots
(roundtrip y purga), generación del mundo, y el tick_actual que usa
Vista_Foco (ver comunicaciones_remoto.py / vista_foco.py) para detectar
"hubo tick nuevo".

El estado espacial ya NO vive en LogicaMundo sino en Mundo (logica.mundo):
  - antes logica._gold_cells ........ ahora logica.mundo.malla_terreno
  - antes logica._elements .......... ahora logica.mundo.elementos
  - antes logica._bot_positions ..... ahora logica.mundo.bots (bot_id ->
    id_elemento) + logica.mundo.ids (id_elemento -> posición)
Los ids son int de Python (ya no numpy.uint64).

Se usa Elemento_Test (Core/Entities/Elementos/elemento_test.py) en vez
de un mock, porque crear_elemento() pasa por reconstruir_elemento()
(registry.py) — un mock no ejercitaría la ruta de (de)serialización
real, que es justamente lo que más interesa comprobar aquí.

Para los tests de avatar de bot se usa un Bot real (no Elemento_Test):
eliminar_avatar_bot depende del stat "id" (bot_id), que solo Bot
declara, y que es DISTINTO del id_elemento del avatar en el mundo (ver
logica_mundo::_bot_id_de) — usar Elemento_Test ahí ocultaría
justamente la separación entre ambos ids que estos tests deben cubrir.
"""

import json

import pytest

import Config.settings as config
from Core.Entities.Elementos.elemento_test import Elemento_Test
from Core.Entities.Elementos.Simples.Bot.bot import Bot
from Infraestructura.Gestores.Mundo.LogicaMundo.logica_mundo import (
    EstadoGeneracion,
    LogicaMundo,
)


def _elemento_test_dict(eid: int, casilla: tuple[int, int] = (0, 0)) -> dict:
    """
    Instancia un Elemento_Test real (con su id_elemento y comportamientos
    reales) y lo serializa con serializar() — no se construye el dict a
    mano para no arriesgarse a que el blob de prueba quede desincronizado
    de lo que Elemento_Test.serializar() produce de verdad.
    """
    elemento = Elemento_Test(casilla=casilla, id_elemento=eid, peso=1.0)
    return elemento.serializar()


def _elemento_test_bytes(eid: int, casilla: tuple[int, int] = (0, 0)) -> bytes:
    """Blob serializado mínimo que crear_elemento() espera, ya con
    '__clase__', 'id_elemento' y 'comportamientos' coherentes entre sí."""
    return json.dumps(_elemento_test_dict(eid, casilla)).encode()


def _bot_test_bytes(
    id_elemento: int, id_bot: int, casilla: tuple[int, int] = (0, 0)
) -> bytes:
    """
    Blob de un Bot real y completo, serializado con su propio
    serializar() — igual criterio que _elemento_test_bytes: nunca a
    mano, para no desincronizarse del formato real.

    id_elemento (avatar en el mundo) e id_bot (script en GestorBots) se
    piden por separado y deliberadamente distintos en las llamadas de
    este módulo, para cubrir justo la separación entre ambos ids.
    """
    bot = Bot(
        id_elemento=id_elemento,
        stats_script={
            "armadura": 1,
            "grasa": 1,
            "longevidad": 1,
            "movilidad": 1,
            "percepcion": 1,
        },
        id_bot=id_bot,
        tamanho=1,
        casilla=casilla,
        rotacion=0.0,
    )
    return json.dumps(bot.serializar()).encode()


class _GestorBotsFalso:
    """Sustituto mínimo de GestorBotsClientAsync: solo anota a qué bots se
    les pidió terminar el script."""

    def __init__(self) -> None:
        self.matados: list[int] = []

    async def matar_script_bot(self, bot_id: int) -> None:
        self.matados.append(bot_id)


@pytest.fixture
def logica() -> LogicaMundo:
    # gestor_bots_client=None es válido salvo para matar_bot, que tiene sus
    # propios tests con _GestorBotsFalso.
    return LogicaMundo(gestor_bots_client=None)


# ── Elementos ──


@pytest.mark.unit
async def test_crear_elemento_suelo_ok(logica: LogicaMundo):
    ok, error = await logica.crear_elemento(
        pos=(3, 4), type_id="suelo", element=_elemento_test_bytes(eid=1)
    )
    assert ok is True
    assert error == ""
    assert (3, 4) in logica.mundo.malla_terreno
    assert logica.mundo.malla_terreno[(3, 4)].suelo == 1


@pytest.mark.unit
async def test_crear_elemento_bot_registra_bot_y_posicion(logica: LogicaMundo):
    # bot_id (99) e id_elemento (42) distintos a propósito: mundo.bots va de
    # bot_id a id_elemento, y la posición se busca después por id_elemento.
    ok, _ = await logica.crear_elemento(
        pos=(5, 5),
        type_id="bot",
        element=_bot_test_bytes(id_elemento=42, id_bot=99),
    )
    assert ok is True
    assert logica.mundo.bots[99] == 42
    assert logica.mundo.obtener_posicion(42) == (5, 5)


@pytest.mark.unit
async def test_crear_elemento_sin_id_falla(logica: LogicaMundo):
    # Se parte de un blob válido y se elimina 'id_elemento' a posteriori,
    # para seguir probando justo el caso "falta el id" sin tener que
    # reconstruir el resto del dict a mano.
    data = _elemento_test_dict(eid=1)
    del data["id_elemento"]
    ok, error = await logica.crear_elemento(
        pos=(0, 0), type_id="suelo", element=json.dumps(data).encode()
    )
    assert ok is False
    assert "id_elemento" in error.lower()


@pytest.mark.unit
async def test_eliminar_elemento_vacia_celda_si_queda_sin_slots(logica: LogicaMundo):
    await logica.crear_elemento(
        pos=(1, 1), type_id="suelo", element=_elemento_test_bytes(1)
    )
    ok, _ = await logica.eliminar_elemento(pos=(1, 1), element_id=1)
    assert ok is True
    assert (
        1,
        1,
    ) not in logica.mundo.malla_terreno, "la celda debe desaparecer si queda vacía"


@pytest.mark.unit
async def test_eliminar_elemento_desconocido_falla(logica: LogicaMundo):
    await logica.crear_elemento(
        pos=(2, 2), type_id="suelo", element=_elemento_test_bytes(1)
    )
    ok, error = await logica.eliminar_elemento(pos=(2, 2), element_id=999)
    assert ok is False
    assert "no encontrado" in error.lower()


@pytest.mark.unit
async def test_asignar_id_devuelve_int_y_crece(logica: LogicaMundo):
    primero = await logica.asignar_id()
    segundo = await logica.asignar_id()
    assert isinstance(primero, int)
    assert isinstance(segundo, int)
    assert segundo == primero + 1


# ── Bots ──


@pytest.mark.unit
async def test_eliminar_avatar_bot_limpia_el_indice_de_bots(logica: LogicaMundo):
    # id_bot (10) distinto de id_elemento (77): cubre la separación real
    # entre el id del script y el del avatar.
    await logica.crear_elemento(
        pos=(7, 7),
        type_id="bot",
        element=_bot_test_bytes(id_elemento=77, id_bot=10),
    )
    ok, _ = await logica.eliminar_avatar_bot(bot_id=10)
    assert ok is True
    assert 10 not in logica.mundo.bots
    assert logica.mundo.obtener_posicion(77) is None


@pytest.mark.unit
async def test_eliminar_avatar_bot_desconocido_falla(logica: LogicaMundo):
    # bot_id es numérico en todo el sistema; se usa un id que no existe.
    ok, error = await logica.eliminar_avatar_bot(bot_id=999999)
    assert ok is False
    assert "no encontrado" in error.lower()


@pytest.mark.unit
async def test_matar_bot_termina_el_script_aunque_el_avatar_ya_no_exista():
    """
    Caso normal, no una rareza: cuando un Sector informa de una muerte, el
    avatar ya se quitó al aplicar las celdas. matar_bot debe terminar el
    script igualmente (antes devolvía False sin hacerlo).
    """
    falso = _GestorBotsFalso()
    logica = LogicaMundo(gestor_bots_client=falso)

    ok, _ = await logica.matar_bot(bot_id=123, cause="test", tick_id=1)

    assert ok is True
    assert falso.matados == [123]


@pytest.mark.unit
async def test_matar_bot_elimina_avatar_y_termina_el_script():
    falso = _GestorBotsFalso()
    logica = LogicaMundo(gestor_bots_client=falso)
    await logica.crear_elemento(
        pos=(7, 7),
        type_id="bot",
        element=_bot_test_bytes(id_elemento=77, id_bot=10),
    )

    ok, _ = await logica.matar_bot(bot_id=10, cause="test", tick_id=1)

    assert ok is True
    assert 10 not in logica.mundo.bots
    assert falso.matados == [10]


# ── Snapshots ──


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
        pos=(9, 9), type_id="suelo", element=_elemento_test_bytes(99)
    )
    await logica.save_snapshot("test_snap")

    logica2 = LogicaMundo(gestor_bots_client=None)
    logica2.SNAPSHOT_DIR = snapshot_dir_aislado
    ok, error = await logica2.load_state("test_snap")

    assert ok is True, error
    assert (9, 9) in logica2.mundo.malla_terreno
    assert logica2.mundo.malla_terreno[(9, 9)].suelo == 99
    assert 99 in logica2.mundo.elementos


@pytest.mark.unit
async def test_load_state_snapshot_inexistente_devuelve_error(
    logica: LogicaMundo, snapshot_dir_aislado
):
    """Antes no lanzaba y el RPC respondía ok=True aunque no existiera el
    snapshot. Ahora devuelve (False, mensaje) y no toca el mundo."""
    logica.SNAPSHOT_DIR = snapshot_dir_aislado

    ok, error = await logica.load_state("no_existe_este_id")

    assert ok is False
    assert "no encontrado" in error.lower()
    assert logica.mundo.malla_terreno == {}


@pytest.mark.unit
def test_purgar_no_borra_nada_si_hay_menos_snapshots_que_el_maximo(
    logica: LogicaMundo, snapshot_dir_aislado, monkeypatch
):
    """Regresión: sin max(0, ...), con 15 snapshots y SNAPSHOT_MAX=20 el
    corte [:-5] borraba los 10 más antiguos."""
    logica.SNAPSHOT_DIR = snapshot_dir_aislado
    monkeypatch.setattr(config, "SNAPSHOT_MAX", 20)
    for i in range(15):
        (snapshot_dir_aislado / f"logica_mundo_{i:010d}.json").write_text("{}")

    logica._purgar_snapshots_antiguos()

    assert len(list(snapshot_dir_aislado.glob("logica_mundo_*.json"))) == 15


@pytest.mark.unit
def test_purgar_borra_los_mas_antiguos_si_se_pasa_del_maximo(
    logica: LogicaMundo, snapshot_dir_aislado, monkeypatch
):
    logica.SNAPSHOT_DIR = snapshot_dir_aislado
    monkeypatch.setattr(config, "SNAPSHOT_MAX", 20)
    for i in range(25):
        (snapshot_dir_aislado / f"logica_mundo_{i:010d}.json").write_text("{}")

    logica._purgar_snapshots_antiguos()

    quedan = sorted(p.name for p in snapshot_dir_aislado.glob("logica_mundo_*.json"))
    assert len(quedan) == 20
    assert quedan[0] == "logica_mundo_0000000005.json", "se borran los 5 más antiguos"


# ── Generación del mundo ──


@pytest.mark.unit
async def test_generar_mundo_crea_atmosfera_y_suelo(logica: LogicaMundo, monkeypatch):
    """
    Mundo pequeño (20x20, escala 10 -> 2x2 celdas de atmósfera). Comprueba
    también que "Suelo_Piedra" es un nombre registrado y construible por
    nombre (el generador lo da por supuesto).
    """
    monkeypatch.setattr(config, "GRID_WIDTH", 20)
    monkeypatch.setattr(config, "GRID_HEIGHT", 20)
    monkeypatch.setattr(config, "ATMOSFERA_ESCALA", 10)

    assert logica.estado_generacion()[0] == EstadoGeneracion.NO_INICIADA

    ok, error = await logica.generar_mundo()
    assert ok is True, error
    await logica._tarea_generacion  # espera a que termine la tarea de fondo

    estado, progreso, error_generacion = logica.estado_generacion()
    assert estado == EstadoGeneracion.COMPLETADA, error_generacion
    assert progreso == 1.0
    assert len(logica.mundo.malla_atmosfera) == 4
    assert len(logica.mundo.malla_terreno) == 400


@pytest.mark.unit
async def test_generar_mundo_rechaza_una_segunda_llamada_en_curso(
    logica: LogicaMundo, monkeypatch
):
    monkeypatch.setattr(config, "GRID_WIDTH", 20)
    monkeypatch.setattr(config, "GRID_HEIGHT", 20)

    ok, _ = await logica.generar_mundo()
    assert ok is True

    # Sin ceder el control todavía: la tarea de fondo no ha empezado, el
    # estado ya es EN_CURSO.
    ok2, error2 = await logica.generar_mundo()
    assert ok2 is False
    assert "en curso" in error2.lower()

    await logica._tarea_generacion


# ── tick_actual — lo necesita Vista_Foco (FocoBroadcaster) ──


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
