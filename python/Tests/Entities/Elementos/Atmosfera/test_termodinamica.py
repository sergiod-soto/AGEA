# Tests/Fisica/test_termodinamica.py
"""
Pruebas de Core/Fisica/termodinamica.py: saturación, su derivada y el ajuste
de fase (condensación / evaporación de nube). Funciones puras: sin fixtures.
"""

import pytest

from Config.parametros_simulacion import CALENTAMIENTO_POR_CONDENSACION
from Core.Fisica.termodinamica import (
    ajuste_saturacion,
    celsius_a_kelvin,
    densidad_vapor_saturacion,
    derivada_densidad_vapor_saturacion,
    autoconversion,
)

T_20C = celsius_a_kelvin(20.0)


def test_derivada_coincide_con_diferencia_finita():
    # Dentro del rango de Magnus la derivada analítica debe coincidir con la
    # numérica (diferencia central). Si no, el denominador de ajuste_saturacion
    # estaría mal y la condensación no igualaría la saturación.
    h = 0.01
    numerica = (
        densidad_vapor_saturacion(T_20C + h) - densidad_vapor_saturacion(T_20C - h)
    ) / (2 * h)
    assert derivada_densidad_vapor_saturacion(T_20C) == pytest.approx(
        numerica, rel=1e-4
    )


def test_aire_subsaturado_sin_nube_no_cambia():
    vapor = 0.5 * densidad_vapor_saturacion(T_20C)
    assert ajuste_saturacion(vapor, 0.0, T_20C) == 0.0


def test_sobresaturacion_condensa_y_deja_el_aire_en_saturacion():
    # Con poca sobresaturación la linealización es muy buena: tras mover
    # delta a nube y calentar k·delta, el vapor restante debe quedar (casi) en
    # la saturación a la NUEVA temperatura.
    sat = densidad_vapor_saturacion(T_20C)
    vapor = 1.1 * sat
    delta = ajuste_saturacion(vapor, 0.0, T_20C)
    assert delta > 0
    sat_nueva = densidad_vapor_saturacion(
        T_20C + CALENTAMIENTO_POR_CONDENSACION * delta
    )
    assert (vapor - delta) == pytest.approx(sat_nueva, abs=0.02 * sat)


def test_nunca_condensa_mas_vapor_del_que_hay():
    # Sobresaturación enorme con poco vapor total no puede dar delta > vapor.
    delta = ajuste_saturacion(1e-6, 0.0, celsius_a_kelvin(-40.0))
    assert delta <= 1e-6


def test_nube_se_evapora_hasta_agotarse():
    # Aire seco y poca nube: se evapora toda (delta == -nube), no más.
    nube = 1e-3
    assert ajuste_saturacion(0.0, nube, T_20C) == -nube


def test_nube_se_evapora_solo_parcialmente():
    # Mucha nube y aire a medio saturar: evapora algo, pero no toda.
    sat = densidad_vapor_saturacion(T_20C)
    nube = 10 * sat
    delta = ajuste_saturacion(0.5 * sat, nube, T_20C)
    assert -nube < delta < 0


def test_temperatura_no_positiva_lanza_error():
    with pytest.raises(ValueError):
        ajuste_saturacion(0.01, 0.0, 0.0)


def test_autoconversion_bajo_umbral_no_llueve():
    assert autoconversion(5e-5, 1e-4, 3600.0, 1.0) == 0.0


def test_autoconversion_sobre_umbral():
    # exceso 2e-4 kg/m³ · dt/tau = 1/3600
    assert autoconversion(3e-4, 1e-4, 3600.0, 1.0) == pytest.approx(2e-4 / 3600.0)


def test_autoconversion_nunca_supera_la_nube():
    # dt/tau = 1 y umbral 0: se convierte toda la nube, ni un gramo más.
    assert autoconversion(3e-4, 0.0, 1.0, 1.0) == pytest.approx(3e-4)
