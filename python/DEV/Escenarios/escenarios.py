# Dev/Escenarios/escenarios.py
"""
escenarios.py — Registro de escenarios de inicialización para pruebas.

Ver Serie_Estados.py (mismo directorio): aquí solo se registran
"recetas" que rellenan una Serie_Estados con estados, indexadas por
nombre. Un escenario nuevo es una entrada en ESCENARIOS, sin tocar
el motor.
"""

from __future__ import annotations

from typing import Callable

from Core.Entities.Elementos.Abstractos.Bioma.Suelo.suelo_piedra import Suelo_Piedra
from Dev.Escenarios.serie_estados import Serie_Estados
from Core.Entities.Elementos.elemento_test import Elemento_Test

TipoEscenario = Callable[[Serie_Estados], None]


def _escenario_suelo(serie: Serie_Estados) -> None:
    """
    Malla de NxN Suelos, desde (0,0) hasta (n-1, n-1).
    N se define aquí mismo (n=4); para otro tamaño, cambiar este valor
    -- ver conversación: se descartó parametrizarlo por función porque
    de momento solo hace falta un tamaño fijo.
    """
    n = 10

    async def crear():
        for i in range(n):
            for j in range(n):
                await serie.Crear_Elemento(
                    Suelo_Piedra,
                    casilla=(i, j),
                    type_id="Suelo_Piedra",
                )

    serie.add([crear])


def _escenario_elemento_test_1(serie: Serie_Estados) -> None:
    """
    Escenario mínimo: un único Elemento_Test en (0, 0) y nada más.
    Pensado para probar de punta a punta que Logica_Mundo recibe el
    elemento y que Unity acaba representándolo -- no crea bots ni
    ningún otro comportamiento.
    """

    async def crear():
        await serie.Crear_Elemento(
            Elemento_Test,
            casilla=(0, 0),
            peso=1.0,
        )

    serie.add([crear])


def _escenario_elemento_test_100(serie: Serie_Estados) -> None:

    async def crear():
        for i in range(10):
            for j in range(10):
                await serie.Crear_Elemento(
                    Elemento_Test,
                    casilla=(i, j),
                    peso=1.0,
                )

    serie.add([crear])


def _escenario_elemento_test_cuadrado(serie: Serie_Estados) -> None:
    """
    Un Elemento_Test recorre en bucle el perímetro de un cuadrado de
    10x10 empezando en (0,0):
        (0,0) -> (10,0) -> (10,10) -> (0,10) -> (0,0) -> ...
    """
    lado = 2
    esquinas = [(0, 0), (lado, 0), (lado, lado), (0, lado)]

    async def paso(elemento, indice: int):
        siguiente = esquinas[indice % len(esquinas)]
        await serie.Mover_Elemento_Logica(elemento, siguiente)
        serie.add([lambda: paso(elemento, indice + 1)])

    async def crear_y_empezar():
        elemento = await serie.Crear_Elemento(Elemento_Test, casilla=(0, 0), peso=1.0)
        serie.add([lambda: paso(elemento, 1)])

    serie.add([crear_y_empezar])


# Nombre -> función que puebla el escenario.
ESCENARIOS: dict[str, TipoEscenario] = {
    "escenario_suelo": _escenario_suelo,
    "escenario_elemento_test_1": _escenario_elemento_test_1,
    "escenario_elemento_test_100": _escenario_elemento_test_100,
    "escenario_elemento_test_cuadrado": _escenario_elemento_test_cuadrado,
}


def cargar_escenario(nombre: str, serie: Serie_Estados) -> None:
    """Busca `nombre` en el registro y lo aplica sobre `serie`."""
    escenario = ESCENARIOS.get(nombre)
    if escenario is None:
        raise KeyError(
            f"Escenario desconocido: '{nombre}'. Válidos: {list(ESCENARIOS)}"
        )
    escenario(serie)
