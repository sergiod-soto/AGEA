"""
Gestores/Mundo/api_acciones.py — Registro central de acciones del mundo.

Para añadir una acción nueva:
  1. Crear script en Gestores/Mundo/Acciones/mi_accion.py
  2. Importarlo aquí y añadirlo a ACCIONES

Convenciones:
  - funcion_hv:    síncrona. None si la acción no es delegable al HV.
  - funcion_mundo: async.    None si la acción no llega al mundo.
"""

from __future__ import annotations
from dataclasses import dataclass
from Gestores.Mundo.Acciones.mirar import mirar

# ---------------------------------------------------------------------------
# Tipos compartidos
# ---------------------------------------------------------------------------





@dataclass
class AccionContext:
    """
    Contexto unificado para funciones de ACCIONES.

    Campos comunes
    --------------
    bot_id  : identificador del bot que realiza la acción.
    payload : bytes enviados por el bot en el request.

    Campos del Mundo (None si ejecuta el HV)
    ----------------------------------------
    gold_cells    : estado gold del mundo — solo lectura por convención.
    elements      : elementos físicos del mundo — solo lectura por convención.
    bot_positions : posiciones de bots — solo lectura por convención.
    """

    bot_id: str
    payload: bytes
    gold_cells: dict | None = None
    elements: dict | None = None
    bot_positions: dict | None = None


# ---------------------------------------------------------------------------
# Registro de acciones
# ---------------------------------------------------------------------------

ACCIONES: dict[str, dict] = {
    "mirar": {
        "coste": 1,
        "descripcion": (
            "Lanza un rayo desde la posición del bot en la dirección de su rotación "
            "hasta la distancia indicada. Devuelve los colores RGB de la primera "
            "celda bloqueante, o [[0,0,0]] si no hay nada."
        ),
        "funcion": mirar,
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_coste(action_name: str) -> int:
    entrada = ACCIONES.get(action_name)
    return entrada["coste"] if entrada else 0


def accion_conocida(action_name: str) -> bool:
    return action_name in ACCIONES


def listar() -> list[str]:
    return list(ACCIONES.keys())
