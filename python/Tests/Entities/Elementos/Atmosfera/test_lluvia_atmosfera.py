# Tests/Entities/Mundo/Atmosfera/test_lluvia_atmosfera.py

import pytest

from Config import validacion_simulacion
from Config.parametros_simulacion import (
    ALTURA_CAPA_AIRE,
    NUBE_CRITICA,
    SEGUNDOS_SIMULADOS_TICK,
    TAU_LLUVIA,
)
from Core.Entities.Mundo.Atmosfera.sistema_atmosferico import _precipitar
from Infraestructura.Gestores.Transporte.celda_atmosfera_proto import (
    a_proto,
    desde_proto,
)


def test_sin_exceso_de_nube_no_llueve(celda_atmosfera):
    celda_atmosfera.nube.valor = NUBE_CRITICA / 2
    _precipitar(celda_atmosfera)
    assert celda_atmosfera.lluvia.valor == 0.0
    assert celda_atmosfera.nube.valor == pytest.approx(NUBE_CRITICA / 2)


def test_precipitar_baja_nube_y_sube_lluvia(celda_atmosfera):
    celda_atmosfera.nube.valor = NUBE_CRITICA + 2e-4
    _precipitar(celda_atmosfera)
    llovido = 2e-4 * SEGUNDOS_SIMULADOS_TICK / TAU_LLUVIA
    assert celda_atmosfera.nube.valor == pytest.approx(NUBE_CRITICA + 2e-4 - llovido)
    assert celda_atmosfera.lluvia.valor == pytest.approx(llovido * ALTURA_CAPA_AIRE)


def test_lluvia_se_reinicia_cada_tick(celda_atmosfera):
    # Se ASIGNA, no se acumula: un tick sin lluvia deja 0.
    celda_atmosfera.lluvia.valor = 5.0
    celda_atmosfera.nube.valor = 0.0
    _precipitar(celda_atmosfera)
    assert celda_atmosfera.lluvia.valor == 0.0


def test_proto_conserva_la_lluvia(celda_atmosfera):
    celda_atmosfera.lluvia.valor = 0.37
    assert desde_proto(a_proto(celda_atmosfera)).lluvia.valor == pytest.approx(0.37)


def test_representar_incluye_lluvia(celda_atmosfera):
    celda_atmosfera.lluvia.valor = 0.37
    assert celda_atmosfera.representar()["lluvia"] == pytest.approx(0.37)


@pytest.mark.parametrize("tau", [0.0, -1.0, 0.5])
def test_estabilidad_rechaza_tau_invalido(monkeypatch, tau):
    monkeypatch.setattr(validacion_simulacion, "TAU_LLUVIA", tau)
    with pytest.raises(ValueError, match="lluvia"):
        validacion_simulacion.validar_estabilidad()
