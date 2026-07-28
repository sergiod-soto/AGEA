# Tests/Core/Entities/Elementos/test_registry_coherencia.py
"""
Valida que los dos registros de nombre -> clase (ELEMENTOS y
COMPORTAMIENTOS) no colisionen entre sí.

Por qué importa: reconstruir_elemento() resuelve "__clase__" contra
ELEMENTOS y cada nombre de "comportamientos" contra COMPORTAMIENTOS. Si
el mismo nombre de clase existiera registrado en AMBOS diccionarios
apuntando a clases distintas, la reconciliación de comportamientos
dinámicos (ver registry.reconstruir_elemento) podría reconstruir en
silencio con la clase equivocada — sin ningún error visible — en vez de
fallar de forma ruidosa. Este test detecta esa situación en CI, antes de
que aparezca como un bug real en un roundtrip de producción.
"""

from __future__ import annotations

from Core.Entities.Elementos.registry import ELEMENTOS
from Core.Entities.Comportamiento.registry import COMPORTAMIENTOS


def test_elementos_y_comportamientos_no_comparten_nombres():
    """
    Ambos registros deben tener claves disjuntas: un nombre de clase no
    puede significar "elemento completo" y "comportamiento suelto" a la
    vez, porque reconstruir_elemento() decide en qué registro buscar
    según el contexto (__clase__ vs. claves de "comportamientos"), no
    según el nombre en sí.
    """
    solapados = set(ELEMENTOS.keys()) & set(COMPORTAMIENTOS.keys())
    assert not solapados, (
        f"Nombres registrados a la vez en ELEMENTOS y COMPORTAMIENTOS: "
        f"{sorted(solapados)} — reconstruir_elemento() podría resolver "
        f"contra la clase equivocada según el contexto."
    )


def test_cada_nombre_de_registro_coincide_con_su_clase():
    """
    Comprobación complementaria: la clave con la que se registra cada
    clase debe coincidir con su __name__ real. Si un día alguien
    registra una clase bajo un alias distinto a su nombre real, "__clase__"
    (que siempre se genera a partir de type(self).__name__ al serializar,
    ver Elemento.serializar) dejaría de encontrarla — un roundtrip
    real fallaría con 'Clase de elemento desconocida', o peor, resolvería
    silenciosamente otra clase que sí coincida por casualidad de nombre.
    """
    for nombre, clase in {**ELEMENTOS, **COMPORTAMIENTOS}.items():
        assert clase.__name__ == nombre, (
            f"'{nombre}' registrado, pero la clase real se llama "
            f"'{clase.__name__}' — deben coincidir."
        )
