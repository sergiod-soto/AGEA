# Infraestructura/Gestores/Mundo/Sector/mutaciones.py
"""
Tipos de mutación que un elemento puede pedir durante su tick().

Por qué existen como tipos separados en vez de aplicar el cambio directamente:
  Sector nunca es la fuente de verdad del estado del mundo (eso vive en
  Logica_Mundo, ver logica_mundo.py: _gold_cells / _elements). Si tick()
  escribiera directamente sobre algún diccionario del Sector, ese cambio se
  perdería al final del tick (Sector no persiste nada — se retiraron los
  snapshots de sector por ser estado transitorio) y Logica_Mundo nunca se
  enteraría de que ocurrió.

  Por eso cada mutación se representa como un dato (no como una llamada que
  ya se ejecutó), se acumula en TickContext y solo se aplica de verdad en
  Logica_Mundo, al recibir el TickDelta completo del sector.
"""

from dataclasses import dataclass
from typing import Any, Union


@dataclass
class CrearElemento:
    """Petición de crear un elemento nuevo en una celda.

    marcador_local identifica a este elemento SOLO dentro de este tick y
    este sector — no es un id real. Hace falta porque un mismo sector puede
    crear varios elementos en el mismo tick (dos reproducciones a la vez,
    por ejemplo): un único valor especial (tipo id=None) no bastaría para
    distinguir cuál-es-cuál cuando Logica_Mundo les asigne id real.
    El elemento se vuelve interactuable recién en el siguiente tick, así
    que no hace falta que Logica_Mundo devuelva el id real de inmediato.
    """

    marcador_local: str
    pos: tuple[int, int]
    tipo_slot: str  # "suelo" | "bot" | "resto"
    elemento: Any  # objeto Elemento ya construido, todavía sin id real


@dataclass
class EliminarElemento:
    """Petición de eliminar un elemento existente (ya tiene id real,
    porque para eliminar algo hace falta que ya existiera al empezar
    el tick)."""

    pos: tuple[int, int]
    id_elemento: int


@dataclass
class MoverElemento:
    """Petición de mover un elemento existente de una celda a otra.

    El movimiento puede terminar cruzando la frontera del sector (migración).
    Eso lo detecta y resuelve Logica_Mundo al aplicar la mutación — el
    Sector que la generó no necesita saber a qué otro sector pertenece
    pos_destino, solo pedir el movimiento.
    """

    id_elemento: int
    pos_origen: tuple[int, int]
    pos_destino: tuple[int, int]


# Unión de todas las mutaciones posibles. Se usa para tipar la lista interna
# de TickContext y el campo `mutaciones` del TickDelta que viaja a Logica_Mundo.
Mutacion = Union[CrearElemento, EliminarElemento, MoverElemento]
