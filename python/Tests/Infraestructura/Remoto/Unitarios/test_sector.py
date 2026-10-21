# Tests/Infraestructura/Remoto/Unitarios/test_sector.py

"""
Tests unitarios de Sector (ciclo de vida, carga/descarga de estado, tick,
resolución de mutaciones y parches de atmósfera). Sin red ni disco.

Los movimientos ENTRE sectores (recibir_elemento / confirmar_salida) están en
test_sector_movimiento.py. Aquí solo se declara el movimiento saliente.

Algunos tests miran self._celdas del Sector (privado) a propósito: es la copia
de trabajo, y comprobarla directamente evita depender de la serialización.
Se asume que Suelo_Piedra vive en Core/Entities/Mundo/Suelo/suelo_piedra.py
(por analogía con suelo_barro.py); si no, solo cambia ese import.
"""

import json
from types import SimpleNamespace

import pytest
from vectors import Vector2

from Config.parametros_simulacion import (
    ALTURA_CAPA_AIRE,
    CALOR_LATENTE_VAPORIZACION,
)
from Config.settings import ATMOSFERA_ESCALA, SECTOR_SIZE
from Core.Entities.Mundo.Atmosfera.celda_atmosfera import Celda_Atmosfera
from Core.Entities.Mundo.Suelo.suelo_piedra import Suelo_Piedra
from Infraestructura.Gestores.Mundo.Sector import sector as sector_mod
from Infraestructura.Gestores.Mundo.Sector.mutaciones import (
    CrearElemento,
    EliminarElemento,
    Evaporar,
    MoverElemento,
)
from Infraestructura.Gestores.Mundo.Sector.sector import Sector, TickDelta
from Infraestructura.Gestores.Mundo.Sector.sector_mode import SectorMode
from Infraestructura.Gestores.Transporte.celda_atmosfera_proto import a_proto
from Infraestructura.Gestores.Transporte.Proto_Generated import (
    common_pb2 as common_pb,
)

# ─────────────────────────────────────────────
#  Ayudas
# ─────────────────────────────────────────────


def _cell_con_suelo(pos: tuple[int, int], id_elemento: int) -> common_pb.Cell:
    """Cell proto con un Suelo_Piedra en el slot de suelo, tal como llegaría
    de Logica en LoadState (elemento serializado a JSON en bytes)."""
    suelo = Suelo_Piedra(casilla=pos, id_elemento=id_elemento)
    return common_pb.Cell(
        pos=common_pb.Position(x=pos[0], y=pos[1]),
        suelo=json.dumps(suelo.serializar()).encode(),
    )


def _celda_atmosfera_proto(pos=(0, 0)):
    """AtmosphereCell con los valores por defecto de Celda_Atmosfera."""
    return a_proto(Celda_Atmosfera(posicion=pos, viento_objetivo=Vector2(0, 0)))


def _sector_cargado(*posiciones: tuple[int, int], activo: bool = True) -> Sector:
    """Sector (0,0) con un Suelo_Piedra por posición (ids 101, 102...) y la
    celda de atmósfera (0,0), que cubre todas las posiciones usadas aquí
    (< ATMOSFERA_ESCALA en x e y)."""
    sector = Sector()
    cells = [_cell_con_suelo(p, 101 + i) for i, p in enumerate(posiciones)]
    sector.load_state(cells, [_celda_atmosfera_proto()], [])
    if activo:
        sector.set_mode(SectorMode.ACTIVO)
    return sector


def _suelo_en(sector: Sector, pos: tuple[int, int]):
    celda = sector._celdas.get(*pos)
    return None if celda is None else celda.suelo


# ─────────────────────────────────────────────
#  Construcción y ciclo de vida
# ─────────────────────────────────────────────


def test_sector_nace_inactivo():
    assert Sector()._mode == SectorMode.INACTIVO


def test_set_mode_cambia_el_modo():
    sector = Sector()
    sector.set_mode(SectorMode.ACTIVO)
    assert sector._mode == SectorMode.ACTIVO


def test_escala_que_no_divide_el_sector_falla_al_construir(monkeypatch):
    # Un bloque de atmósfera repartido entre dos Sectores no tiene dueño:
    # debe fallar al arrancar, no a mitad de partida.
    monkeypatch.setattr(sector_mod, "ATMOSFERA_ESCALA", 7)  # 200 % 7 != 0
    with pytest.raises(ValueError, match="ATMOSFERA_ESCALA"):
        Sector()


# ─────────────────────────────────────────────
#  load_state / get_state
# ─────────────────────────────────────────────


def test_load_state_y_get_state_conservan_celdas_y_atmosfera():
    sector = _sector_cargado((0, 0), (1, 0))

    cells, celdas_atmosfera, bots = sector.get_state()

    assert len(cells) == 2
    assert len(celdas_atmosfera) == 1
    assert bots == []


def test_load_state_registra_el_suelo_en_la_atmosfera():
    # Las cachés no viajan por proto: load_state debe reconstruirlas.
    sector = _sector_cargado((0, 0))
    assert sector._celda_atmosfera_de((0, 0)).inercia_termica > 0


def test_load_state_sin_celda_de_atmosfera_falla():
    sector = Sector()
    with pytest.raises(ValueError, match="faltan"):
        sector.load_state([_cell_con_suelo((0, 0), 101)], [], [])


# ─────────────────────────────────────────────
#  compute_tick / get_delta
# ─────────────────────────────────────────────


def test_compute_tick_inactivo_devuelve_delta_vacio_y_no_avanza_atmosfera():
    sector = _sector_cargado((0, 0), activo=False)
    antes = sector._celda_atmosfera_de((0, 0)).temperatura.valor

    delta = sector.compute_tick(7)

    assert delta.tick_id == 7
    assert delta.changed_cells == []
    assert delta.changed_atmosphere_cells == []
    assert sector._celda_atmosfera_de((0, 0)).temperatura.valor == antes


def test_compute_tick_activo_devuelve_la_atmosfera_propia():
    sector = _sector_cargado((0, 0))

    delta = sector.compute_tick(3)

    assert delta.tick_id == 3
    assert len(delta.changed_atmosphere_cells) == 1


def test_get_delta_devuelve_el_ultimo_tick_y_none_para_otro():
    sector = _sector_cargado((0, 0))
    delta = sector.compute_tick(5)

    assert sector.get_delta(5) is delta
    assert sector.get_delta(6) is None


def test_get_delta_sin_ningun_tick_es_none():
    assert Sector().get_delta(0) is None


# ─────────────────────────────────────────────
#  Mutaciones: crear / eliminar / mover
# ─────────────────────────────────────────────


def test_crear_elemento_lo_coloca_y_lo_marca_como_cambiado():
    sector = _sector_cargado((0, 0))
    delta = TickDelta(tick_id=1)
    nuevo = Suelo_Piedra(casilla=(2, 0), id_elemento=150)

    sector._resolver_mutaciones(
        [
            CrearElemento(
                marcador_local="nuevo_0",
                pos=(2, 0),
                tipo_slot="suelo",
                elemento=nuevo,
                bot_id=None,
            )
        ],
        delta,
    )

    assert _suelo_en(sector, (2, 0)).id_elemento == 150
    assert len(delta.changed_cells) == 1


def test_crear_en_slot_ocupado_se_descarta():
    sector = _sector_cargado((0, 0))
    delta = TickDelta(tick_id=1)
    intruso = Suelo_Piedra(casilla=(0, 0), id_elemento=150)

    sector._resolver_mutaciones(
        [
            CrearElemento(
                marcador_local="nuevo_0",
                pos=(0, 0),
                tipo_slot="suelo",
                elemento=intruso,
                bot_id=None,
            )
        ],
        delta,
    )

    assert _suelo_en(sector, (0, 0)).id_elemento == 101  # el original sigue
    assert delta.changed_cells == []


def test_crear_sin_id_es_fatal():
    sector = _sector_cargado((0, 0))
    sin_id = SimpleNamespace(id_elemento=0)  # solo se mira id_elemento

    with pytest.raises(ValueError, match="sin id_elemento"):
        sector._resolver_mutaciones(
            [
                CrearElemento(
                    marcador_local="nuevo_0",
                    pos=(2, 0),
                    tipo_slot="suelo",
                    elemento=sin_id,
                    bot_id=None,
                )
            ],
            TickDelta(tick_id=1),
        )


def test_eliminar_elemento_libera_el_slot():
    sector = _sector_cargado((0, 0))
    delta = TickDelta(tick_id=1)

    sector._resolver_mutaciones(
        [EliminarElemento(id_elemento=101, pos=(0, 0), bot_id=None)], delta
    )

    assert _suelo_en(sector, (0, 0)) is None
    assert len(delta.changed_cells) == 1
    assert delta.changed_cells[0].suelo == b""


def test_mover_dentro_de_la_region_cambia_la_celda():
    sector = _sector_cargado((0, 0))
    delta = TickDelta(tick_id=1)

    sector._resolver_mutaciones(
        [
            MoverElemento(
                id_elemento=101, pos_origen=(0, 0), pos_destino=(1, 0), bot_id=None
            )
        ],
        delta,
    )

    assert _suelo_en(sector, (0, 0)) is None
    assert _suelo_en(sector, (1, 0)).id_elemento == 101
    assert _suelo_en(sector, (1, 0)).casilla == (1, 0)  # el Sector fija la casilla
    assert len(delta.changed_cells) == 2  # origen y destino


def test_mover_a_slot_ocupado_se_rechaza_y_vuelve_al_origen():
    sector = _sector_cargado((0, 0), (1, 0))  # ids 101 y 102
    delta = TickDelta(tick_id=1)

    sector._resolver_mutaciones(
        [
            MoverElemento(
                id_elemento=101, pos_origen=(0, 0), pos_destino=(1, 0), bot_id=None
            )
        ],
        delta,
    )

    assert _suelo_en(sector, (0, 0)).id_elemento == 101
    assert _suelo_en(sector, (1, 0)).id_elemento == 102
    assert _suelo_en(sector, (0, 0)).casilla == (0, 0)


def test_mover_fuera_de_la_region_se_declara_y_no_toca_el_origen():
    sector = _sector_cargado((0, 0))
    delta = TickDelta(tick_id=1)

    sector._resolver_mutaciones(
        [
            MoverElemento(
                id_elemento=101,
                pos_origen=(0, 0),
                pos_destino=(SECTOR_SIZE, 0),  # primera columna del sector vecino
                bot_id=None,
            )
        ],
        delta,
    )

    assert len(delta.movimientos_salientes) == 1
    assert delta.movimientos_salientes[0].pos_destino.x == SECTOR_SIZE
    # Solo confirmar_salida (tras el sí del destino) lo quita del origen.
    assert _suelo_en(sector, (0, 0)).id_elemento == 101


# ─────────────────────────────────────────────
#  Evaporación
# ─────────────────────────────────────────────


def test_evaporar_sube_la_humedad_y_enfria_el_suelo():
    sector = _sector_cargado((0, 0))
    celda = sector._celda_atmosfera_de((0, 0))
    humedad_antes = celda.humedad_absoluta.valor
    t_suelo_antes = celda.temperatura.valor_suelo
    kg_casilla = 0.5

    sector._resolver_mutaciones(
        [Evaporar(pos=(0, 0), kg_por_m2=kg_casilla)], TickDelta(tick_id=1)
    )

    # La casilla es 1 de ATMOSFERA_ESCALA² que forman la celda.
    kg_celda = kg_casilla / ATMOSFERA_ESCALA**2
    assert celda.humedad_absoluta.valor - humedad_antes == pytest.approx(
        kg_celda / ALTURA_CAPA_AIRE
    )
    assert t_suelo_antes - celda.temperatura.valor_suelo == pytest.approx(
        CALOR_LATENTE_VAPORIZACION * kg_celda / celda.inercia_termica
    )


def test_evaporar_es_aditivo_sobre_la_misma_celda():
    sector = _sector_cargado((0, 0), (1, 0))
    celda = sector._celda_atmosfera_de((0, 0))
    antes = celda.humedad_absoluta.valor

    sector._resolver_mutaciones(
        [Evaporar(pos=(0, 0), kg_por_m2=0.5), Evaporar(pos=(1, 0), kg_por_m2=0.5)],
        TickDelta(tick_id=1),
    )

    esperado = 1.0 / ATMOSFERA_ESCALA**2 / ALTURA_CAPA_AIRE
    assert celda.humedad_absoluta.valor - antes == pytest.approx(esperado)


# ─────────────────────────────────────────────
#  Parches de atmósfera (fase 0)
# ─────────────────────────────────────────────


def test_parche_cambia_el_viento_objetivo():
    sector = _sector_cargado((0, 0))
    parche = common_pb.AtmosphereCell(
        pos=common_pb.Position(x=0, y=0),
        viento_objetivo=common_pb.Vector2(x=3.0, y=-1.0),
    )

    sector.aplicar_parches_atmosfera(1, [parche])

    objetivo = sector._atmosfera.get(0, 0).viento_objetivo
    assert (objetivo.x, objetivo.y) == (3.0, -1.0)


def test_parche_para_celda_inexistente_es_fatal():
    sector = _sector_cargado((0, 0))
    parche = common_pb.AtmosphereCell(
        pos=common_pb.Position(x=9, y=9),
        viento_objetivo=common_pb.Vector2(x=1.0, y=0.0),
    )

    with pytest.raises(ValueError, match="no tiene"):
        sector.aplicar_parches_atmosfera(1, [parche])