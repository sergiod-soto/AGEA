# Tests/Infraestructura/Remoto/Unitarios/test_sector_atmosfera.py
"""
Pruebas de Sector._avanzar_atmosfera y Sector._vecinos_atmosfera.

Para no depender del tamaño real del mundo, cada Sector de prueba se reduce a
2x2 celdas de atmósfera (_size = 2 * ATMOSFERA_ESCALA). _col/_row/_size son
atributos normales y las posiciones propias se derivan de ellos, así que dos
Sectores contiguos (col 0 y col 1) comparten una frontera real: cada uno ve
al otro SOLO a través de su ghost zone de atmósfera (protos del inicio del
tick), igual que en ejecución.
"""

import pytest
from vectors import Vector2

from Config.settings import ATMOSFERA_ESCALA
from Core.Entities.Mundo.Atmosfera.celda_atmosfera import Celda_Atmosfera
from Infraestructura.Gestores.Mundo.Sector.sector import Sector
from Infraestructura.Gestores.Transporte import celda_atmosfera_proto as cap

LADO_ATM = 2  # celdas de atmósfera por lado y Sector


def _celda(pos, nube=0.0) -> Celda_Atmosfera:
    """Celda con suelo registrado (Temperatura exige inercia > 0), humedad por
    debajo de la saturación y viento de 1 m/s hacia +x."""
    c = Celda_Atmosfera(pos, Vector2(0, 0))
    c.registrar_suelo(pos, 50.0, 4e5)
    c.humedad_absoluta.valor = 0.005
    c.nube.valor = nube
    c.viento.intensidad = 1.0
    c.viento.direccion = Vector2(1, 0)
    return c


def _sector(col: int, nubes: dict | None = None) -> Sector:
    s = Sector()
    s._col, s._row, s._size = col, 0, LADO_ATM * ATMOSFERA_ESCALA
    nubes = nubes or {}
    for pos in s._posiciones_atmosfera_propias():
        s._atmosfera.set(*pos, _celda(pos, nubes.get(pos, 0.0)))
    return s


def _total_agua(s: Sector) -> float:
    return sum(c.humedad_absoluta.valor + c.nube.valor for _, c in s._atmosfera.items())


def _estados(s: Sector) -> dict:
    from Core.Entities.Mundo.Atmosfera.sistema_atmosferico import EstadoCelda

    return {pos: EstadoCelda.desde_celda(c) for pos, c in s._atmosfera.items()}


# ---------------- _vecinos_atmosfera ----------------


def test_borde_del_mundo_se_omite_y_los_propios_se_incluyen():
    s = _sector(0)
    vecinos = s._vecinos_atmosfera((0, 0), _estados(s))
    # (0,0): hay vecino en +x y +y; -x y -y son borde cerrado (sin ghost).
    assert {(v.direccion.x, v.direccion.y) for v in vecinos} == {(1, 0), (0, 1)}


def test_vecino_de_otro_sector_sale_de_la_ghost_con_nube_y_bloqueo():
    s = _sector(0)
    fantasma = _celda((LADO_ATM, 0), nube=3e-4)  # primera celda del Sector 1
    fantasma.registrar_resistencia_elemento(999, 1.0)  # bloqueo total
    s.set_ghost_zone_atmosfera(1, [cap.a_proto(fantasma)])

    vecinos = s._vecinos_atmosfera((LADO_ATM - 1, 0), _estados(s))
    este = [v for v in vecinos if (v.direccion.x, v.direccion.y) == (1, 0)]

    assert len(este) == 1
    assert este[0].nube == 3e-4
    assert este[0].viento_x == pytest.approx(1.0)
    assert este[0].bloqueo_total_viento is True


# ---------------- _avanzar_atmosfera ----------------


def test_un_sector_aislado_conserva_agua_y_usa_el_estado_congelado():
    # Si _avanzar_atmosfera leyera a los vecinos ya mutados (en vez de
    # estados_previos), lo que sale de una celda no coincidiría con lo que
    # entra en la otra y el total cambiaría.
    s = _sector(0, {(0, 0): 1e-4})
    antes = _total_agua(s)
    s._avanzar_atmosfera(1)
    assert _total_agua(s) == pytest.approx(antes, rel=1e-9)


def test_agua_se_conserva_y_cruza_la_frontera_entre_dos_sectores():
    # La nube está en la última columna del Sector 0, pegada a la frontera, con
    # viento hacia el Sector 1. Cada Sector recibe como ghost el estado del
    # inicio del tick del otro, tomado ANTES de que ninguno avance.
    a = _sector(0, {(LADO_ATM - 1, 0): 1e-4})
    b = _sector(1)

    borde_a = [c for (x, _), c in a._atmosfera.items() if x == LADO_ATM - 1]
    borde_b = [c for (x, _), c in b._atmosfera.items() if x == LADO_ATM]
    a.set_ghost_zone_atmosfera(1, [cap.a_proto(c) for c in borde_b])
    b.set_ghost_zone_atmosfera(1, [cap.a_proto(c) for c in borde_a])

    total_antes = _total_agua(a) + _total_agua(b)
    b_antes = _total_agua(b)

    a._avanzar_atmosfera(1)
    b._avanzar_atmosfera(1)

    assert _total_agua(a) + _total_agua(b) == pytest.approx(total_antes, rel=1e-9)
    assert _total_agua(b) > b_antes  # de verdad hubo transporte entre Sectores
