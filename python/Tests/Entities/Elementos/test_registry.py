# Tests/Entities/Unitarios/test_registry.py
"""
test_registry.py — Comprueba que registry.py se importa sin fallar
(guarda contra el import circular que ya rompió el arranque real de
Logica_Mundo una vez, ver conversación previa sobre elemento_abstracto.py)
y que ELEMENTOS mapea nombres a clases reales, no a None ni a basura.
"""

import pytest


@pytest.mark.unit
def test_registry_importa_sin_error():
    """
    Este test, en sí mismo, ya sirve de canario: si algún día se
    reintroduce un ciclo de imports en Core/Entities, este import
    fallará aquí con un traceback claro, en vez de descubrirse recién
    al arrancar logica_mundo_server.py en producción.
    """
    from Core.Entities.Elementos.registry import ELEMENTOS, reconstruir_elemento

    assert ELEMENTOS, "ELEMENTOS no debería estar vacío"
    assert callable(reconstruir_elemento)


@pytest.mark.unit
def test_todas_las_clases_de_elementos_son_clases_reales():
    from Core.Entities.Elementos.registry import ELEMENTOS

    for nombre, clase in ELEMENTOS.items():
        assert isinstance(clase, type), f"'{nombre}' no mapea a una clase: {clase!r}"


@pytest.mark.unit
def test_reconstruir_elemento_clase_desconocida_lanza_valueerror():
    from Core.Entities.Elementos.registry import reconstruir_elemento

    with pytest.raises(ValueError, match="Clase de elemento desconocida"):
        reconstruir_elemento({"__clase__": "Esto_No_Existe"})
