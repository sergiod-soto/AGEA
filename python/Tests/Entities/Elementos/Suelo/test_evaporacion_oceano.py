# Tests/Entities/Elementos/Suelo/test_evaporacion_oceano.py
"""
Acuoso (vía Suelo_Oceano): cuánta agua pide evaporar y cuándo falla.
Ajusta el import de densidad_vapor_saturacion a su ubicación real en Core/Fisicas.
"""

import pytest

from Config.parametros_simulacion import ALTURA_CAPA_AIRE
from Core.Entities.Mundo.Suelo.suelo_oceano import Suelo_Oceano
from Core.Fisica.termodinamica import densidad_vapor_saturacion
from Infraestructura.Gestores.Mundo.Sector.mutaciones import Evaporar


def _oceano():
    return Suelo_Oceano(casilla=(0, 0), id_elemento=1)


def test_aire_seco_provoca_evaporacion(crear_ctx):
    ctx = crear_ctx()  # humedad_absoluta = 0
    _oceano().tick(ctx)
    (evap,) = ctx.obtener_mutaciones()
    assert isinstance(evap, Evaporar)
    assert evap.pos == (0, 0) and evap.kg_por_m2 > 0


def test_aire_saturado_no_evapora(crear_ctx, celda_atmosfera):
    celda_atmosfera.humedad_absoluta.valor = (
        1.0  # kg/m³: muy por encima de la saturación
    )
    ctx = crear_ctx()
    _oceano().tick(ctx)
    assert ctx.obtener_mutaciones() == []


def test_tope_por_deficit_del_aire(crear_ctx, celda_atmosfera):
    # Agua mucho más caliente que el aire: el déficit del agua es enorme, pero
    # el aire casi no admite más vapor. Lo evaporado no puede pasar del tope.
    celda_atmosfera.temperatura.valor_suelo = 310.0
    capacidad = 1e-9
    celda_atmosfera.humedad_absoluta.valor = (
        densidad_vapor_saturacion(celda_atmosfera.temperatura.valor) - capacidad
    )
    ctx = crear_ctx()
    _oceano().tick(ctx)
    (evap,) = ctx.obtener_mutaciones()
    assert evap.kg_por_m2 == pytest.approx(capacidad * ALTURA_CAPA_AIRE, rel=1e-6)


def test_una_sola_peticion_por_tick(crear_ctx):
    # Regresión: Oceanico hereda de Acuoso y no debe evaporar dos veces.
    ctx = crear_ctx()
    _oceano().tick(ctx)
    assert len(ctx.obtener_mutaciones()) == 1


def test_sin_celda_de_atmosfera_es_fatal(crear_ctx):
    ctx = crear_ctx(con_atmosfera=False)
    with pytest.raises(RuntimeError):
        _oceano().tick(ctx)


def test_temperatura_cero_es_fatal(crear_ctx, celda_atmosfera):
    celda_atmosfera.temperatura.valor_suelo = 0.0
    ctx = crear_ctx()
    with pytest.raises(ValueError):
        _oceano().tick(ctx)
