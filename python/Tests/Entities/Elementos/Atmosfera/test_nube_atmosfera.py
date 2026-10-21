# Tests/Entities/Mundo/Atmosfera/test_nube_atmosfera.py
"""
Pruebas del sistema de nubes: advección (conservación entre celdas), condensación
en el orquestador, sombra sobre la radiación y persistencia en snapshot.
Usa la fixture `celda_atmosfera` de Tests/conftest.py.
"""

import pytest
from vectors import Vector2

from Config.parametros_simulacion import CALENTAMIENTO_POR_CONDENSACION
from Config.settings import ATMOSFERA_ESCALA, GRID_HEIGHT
from Config.validacion_simulacion import validar_estabilidad
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.nube import (
    Nube,
)
from Core.Entities.Mundo.Atmosfera import sistema_atmosferico as sa
from Core.Entities.Mundo.Atmosfera.celda_atmosfera import Celda_Atmosfera
from Core.Fisica.termodinamica import celsius_a_kelvin, densidad_vapor_saturacion
from Infraestructura.Gestores.Mundo.LogicaMundo.logica_mundo import LogicaMundo


def _vecino(nube, direccion, viento_x=0.0, bloqueo=False):
    """EstadoVecino mínimo (kw_only). Solo importan nube, viento y dirección."""
    return sa.EstadoVecino(
        temperatura=288.15,
        presion=101325.0,
        humedad_absoluta=0.0,
        nube=nube,
        viento_x=viento_x,
        direccion=Vector2(*direccion),
        bloqueo_total_viento=bloqueo,
    )


def _con_suelo(celda: Celda_Atmosfera) -> Celda_Atmosfera:
    # Temperatura.actualizar exige inercia > 0 (sin Suelo registrado falla).
    celda.registrar_suelo((0, 0), 50.0, 4e5)
    return celda


# ---------------- Estabilidad ----------------


def test_estabilidad_con_nube_incluida():
    validar_estabilidad()  # no debe lanzar


# ---------------- Advección ----------------


def test_adveccion_conserva_la_nube_entre_dos_celdas():
    # A y B contiguas (B a la derecha de A), viento 1 m/s hacia B. Cada celda
    # calcula con el estado del inicio del tick de la otra (ghost zone). Lo que
    # sale de A debe entrar en B: la suma no cambia.
    a, b = Nube(1e-3), Nube(0.0)
    a_antes, b_antes = a.valor, b.valor
    v = (1.0, 0.0)

    a.actualizar([_vecino(b_antes, (1, 0), viento_x=1.0)], v, False)
    b.actualizar([_vecino(a_antes, (-1, 0), viento_x=1.0)], v, False)

    assert a.valor < a_antes  # A pierde
    assert b.valor > b_antes  # B gana
    assert a.valor + b.valor == pytest.approx(a_antes + b_antes, rel=1e-12)


def test_sin_viento_la_nube_no_se_mueve():
    n = Nube(1e-3)
    n.actualizar([_vecino(0.0, (1, 0))], (0.0, 0.0), False)
    assert n.valor == 1e-3


def test_bloqueo_total_detiene_la_adveccion():
    n = Nube(1e-3)
    n.actualizar([_vecino(0.0, (1, 0), viento_x=1.0, bloqueo=True)], (1.0, 0.0), False)
    assert n.valor == 1e-3


# ---------------- Condensación (orquestador) ----------------


def test_condensar_conserva_vapor_mas_nube_y_calienta_el_aire():
    celda = _con_suelo(Celda_Atmosfera((0, 0), Vector2(0, 0)))
    celda.temperatura.valor = celsius_a_kelvin(20.0)
    t0 = celda.temperatura.valor
    celda.humedad_absoluta.valor = 1.1 * densidad_vapor_saturacion(t0)
    total_antes = celda.humedad_absoluta.valor + celda.nube.valor

    sa._condensar(celda)

    delta = celda.nube.valor  # la nube partía de 0
    assert delta > 0
    assert celda.humedad_absoluta.valor + celda.nube.valor == pytest.approx(
        total_antes, rel=1e-12
    )
    # Calor latente exacto: ΔTa = k·delta.
    assert celda.temperatura.valor - t0 == pytest.approx(
        CALENTAMIENTO_POR_CONDENSACION * delta, rel=1e-12
    )


def test_condensar_evaporando_la_nube_enfria_el_aire():
    celda = _con_suelo(Celda_Atmosfera((0, 0), Vector2(0, 0)))
    celda.temperatura.valor = celsius_a_kelvin(20.0)
    t0 = celda.temperatura.valor
    celda.nube.valor = 1e-3  # aire seco: la nube se evapora entera

    sa._condensar(celda)

    assert celda.nube.valor == 0.0
    assert celda.humedad_absoluta.valor == pytest.approx(1e-3, rel=1e-12)
    assert celda.temperatura.valor < t0


# ---------------- Sombra sobre la radiación ----------------


def test_factor_nubes_vale_1_sin_nube_y_decrece():
    assert sa._factor_nubes(0.0) == 1.0
    assert 0.0 < sa._factor_nubes(1e-4) < sa._factor_nubes(1e-5) < 1.0


def test_la_nube_reduce_la_radiacion_en_avanzar_celda():
    # Mediodía (progreso_solar 0.25) en el ecuador, equinoccio (anual 0.25).
    fila_ecuador = GRID_HEIGHT // ATMOSFERA_ESCALA // 2

    def radiacion(nube):
        celda = _con_suelo(Celda_Atmosfera((0, fila_ecuador), Vector2(0, 0)))
        celda.nube.valor = nube
        sa.avanzar_celda(celda, 0.25, 0.25, [])
        return celda.radiacion

    sin_nube, con_nube = radiacion(0.0), radiacion(1e-4)
    assert sin_nube > 0
    # La radiación usa la nube del inicio del tick: ratio = transmitancia.
    assert con_nube / sin_nube == pytest.approx(sa._factor_nubes(1e-4), rel=1e-9)


# ---------------- Persistencia ----------------


def test_snapshot_roundtrip_conserva_la_nube():
    celda = Celda_Atmosfera((3, 4), Vector2(1, 2))
    celda.nube.valor = 2.5e-4
    d = LogicaMundo._atmosfera_a_dict(celda)
    assert d["nube"] == 2.5e-4
    assert LogicaMundo._atmosfera_desde_dict((3, 4), d).nube.valor == 2.5e-4


def test_snapshot_sin_nube_se_rechaza():
    # Formato antiguo: load_state lo captura como KeyError y lo rechaza limpio.
    d = LogicaMundo._atmosfera_a_dict(Celda_Atmosfera((0, 0), Vector2(0, 0)))
    del d["nube"]
    with pytest.raises(KeyError):
        LogicaMundo._atmosfera_desde_dict((0, 0), d)
