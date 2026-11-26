# Tests/Infraestructura/Gestores/test_generador_mundo_modular.py

import pytest
from Services.Mundo.generacion_suelos import (
    GeneradorMundo,
    ParametrosGeneracion,
    generar_mapa_suelos,
)


def test_generador_modular_produce_resultado_identico():
    seed = 1234
    ancho, alto = 30, 30
    p = ParametrosGeneracion(seed=seed, ancho=ancho, alto=alto, num_rios=2)

    # 1. Ejecución monolítica estándar
    res1, hidro1, alt1, mont1, red1 = generar_mapa_suelos(parametros=p)

    # 2. Ejecución modular paso a paso
    gen = GeneradorMundo(parametros=p)
    # Paso 1
    m1 = gen.etapa_orografia()
    assert m1.elevacion[0][0] is not None
    # Antes de biomas, los suelos aún no están asignados (excepto mares/lagos)
    assert m1.suelos[15][15] is None or isinstance(m1.suelos[15][15], str)

    # Pasos sucesivos
    gen.etapa_mares_interiores()
    gen.etapa_rios()
    gen.etapa_biomas()
    gen.etapa_barro()
    gen.etapa_limite()

    res2, hidro2, alt2, mont2, red2 = gen.construir_resultado()

    # Deben ser 100% idénticos
    assert res1 == res2
    assert hidro1 == hidro2
    assert alt1 == alt2
    assert mont1 == mont2
    assert red1 == red2


def test_generador_modular_ejecutar_todas_las_etapas():
    gen = GeneradorMundo(seed=999, ancho=20, alto=20)
    gen.ejecutar_todas_las_etapas()
    suelos, hidrologia, alturas, montanas, red = gen.construir_resultado()

    assert len(suelos) == 400
    assert len(alturas) == 400
    assert "rios" in red
    assert "lagos" in red
