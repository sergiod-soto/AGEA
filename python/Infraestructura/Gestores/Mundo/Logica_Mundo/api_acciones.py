# Infraestructura/Gestores/Mundo/Logica_Mundo/api_acciones.py
"""
api_acciones.py — Registro central de acciones del mundo.

Antes vivía en Gestores/Mundo/. Se muda a Logica_Mundo/ porque es quien
ahora resuelve las acciones de los bots (ver logica_mundo.resolver_accion),
y porque el propio AccionContext referencia el estado gold que ahora
vive en Logica_Mundo, no en Gestor_Mundo.

Para añadir una acción nueva:
  1. Crear script en Logica_Mundo/Acciones/mi_accion.py
  2. Importarlo aquí y añadirlo a ACCIONES

Convenciones:
  - funcion_hv:    síncrona. None si la acción no es delegable al HV.
  - funcion_mundo: async.    None si la acción no llega al mundo.
"""

from __future__ import annotations

from dataclasses import dataclass

from Infraestructura.Gestores.Mundo.Logica_Mundo.Acciones.mirar import mirar


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

    Campos de Logica_Mundo (None si ejecuta el HV)
    -----------------------------------------------
    gold_cells    : estado gold — solo lectura por convención.
    elements      : elementos físicos — solo lectura por convención.
    bot_positions : posiciones de bots — solo lectura por convención.

    NOTA: estos tres campos ya no viajan por red — LogicaMundo.resolver_accion
    los pasa por referencia directa a la misma estructura en memoria, dado
    que ahora todo vive en el mismo proceso (ver logica_mundo.py). Se
    mantiene el patrón "solo lectura por convención" en vez de copias
    defensivas para no penalizar el coste por acción, que es precisamente
    la ruta caliente que motivó centralizar aquí este estado.
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
    """Devuelve el coste en puntos de una acción, o 0 si no existe."""
    entrada = ACCIONES.get(action_name)
    return entrada["coste"] if entrada else 0


def accion_conocida(action_name: str) -> bool:
    return action_name in ACCIONES


def listar() -> list[str]:
    return list(ACCIONES.keys())
