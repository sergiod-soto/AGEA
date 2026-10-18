# Infraestructura/Gestores/Mundo/Sector/mutaciones.py

"""
Tipos de mutación que un elemento puede pedir durante su tick().

Por qué son datos y no llamadas ya ejecutadas: si tick() modificara la celda
directamente, el resultado dependería del orden en que se computan los
elementos. Cada mutación se acumula en TickContext (escritura diferida) y
Sector._resolver_mutaciones las aplica sobre su copia de trabajo al terminar
todos los tick(). El resultado viaja a Logica_Mundo (el gold) como
changed_cells; un movimiento a otro Sector viaja como MovimientoSaliente y lo
resuelve el Gestor_Mundo (RecibirElemento / ConfirmarSalida).
"""

from dataclasses import dataclass
from typing import Any, Optional, Union


@dataclass
class CrearElemento:
    """Petición de crear un elemento nuevo en una celda.

    marcador_local identifica al elemento SOLO dentro de este tick y sector;
    no es un id real. PENDIENTE (ids de elementos nacidos en tick(), aplazado):
    Sector._resolver_mutaciones descarta hoy toda creación cuyo elemento no
    tenga id_elemento, así que ninguna creación sin id llega a ejecutarse.
    """

    marcador_local: str
    pos: tuple[int, int]
    tipo_slot: str  # "suelo" | "bot" | "resto"
    elemento: Any  # objeto Elemento ya construido, todavía sin id real
    bot_id: Optional[int] = None


@dataclass
class EliminarElemento:
    """Petición de eliminar un elemento existente (ya tiene id real,
    porque para eliminar algo hace falta que ya existiera al empezar
    el tick)."""

    pos: tuple[int, int]
    id_elemento: int
    bot_id: Optional[int] = None


@dataclass
class MoverElemento:
    """Petición de mover un elemento existente de una celda a otra.

    Si pos_destino cae fuera de la región del Sector, Sector._resolver_mutaciones
    no mueve nada: lo declara como MovimientoSaliente y el Gestor_Mundo lo
    resuelve. El elemento que lo pide solo necesita indicar el destino.
    """

    id_elemento: int
    pos_origen: tuple[int, int]
    pos_destino: tuple[int, int]
    bot_id: Optional[int] = None


@dataclass
class Evaporar:
    """Petición de pasar agua del terreno al aire en una casilla.

    kg_por_m2: masa de agua evaporada en ESTE tick por m² de casilla (>= 0).
    El elemento solo dice cuánta agua pasa; la conversión a humedad (kg/m³) y
    el efecto térmico del calor latente los resuelve el Sector en un único
    sitio (Sector._resolver_mutaciones). Es ADITIVA: varias peticiones sobre la
    misma celda de atmósfera se suman, así que el resultado no depende del
    orden en que tickean los elementos.
    """

    pos: tuple[int, int]  # posición de TERRENO de la casilla
    kg_por_m2: float


Mutacion = Union[CrearElemento, EliminarElemento, MoverElemento, Evaporar]
