# Core/Entities/Comportamiento/Material/registro_transformaciones.py
"""
Nombre -> función de transformación. Cada función recibe SIEMPRE
(propietario, ctx) -- ctx puede ser None fuera de un tick de Sector
(p.ej. si algo llamara a esto directamente desde Logica_Mundo), las
funciones que no lo necesitan simplemente lo ignoran.

Para añadir una transformación nueva: escribirla aquí (o importarla) y
añadirla a REGISTRO_TRANSFORMACIONES.
"""

from typing import Callable

REGISTRO_TRANSFORMACIONES: dict[str, Callable] = {}


def registrar(nombre: str):
    """Decorador para dar de alta una función en el registro sin tener
    que repetir su nombre en dos sitios distintos."""

    def _decorador(funcion):
        REGISTRO_TRANSFORMACIONES[nombre] = funcion
        return funcion

    return _decorador
