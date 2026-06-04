"""
core/acciones.py — Fuente de verdad única de acciones del mundo.

Para añadir una acción nueva al sistema:
  1. Añadirla aquí con su coste y descripción.
  2. Añadir un método de conveniencia en bot_client.py (opcional).
  No hay que tocar ningún otro fichero del sistema de Hypervisores.

Estructura de cada entrada:
  "nombre_accion": {
      "coste":      int,   # puntos que consume por llamada
      "descripcion": str,  # texto libre para documentación
      "funcion": Callable  # la funcion a ejecutar
  }

Reglas de nomenclatura:
  - Minúsculas y guiones bajos.
  - El nombre aquí es exactamente el que el bot manda en ActRequest.action_name
    y el que el Mundo recibe en ForwardActionRequest.action_type.
"""

#
# ------------------------------------------------------------------
# - DEFINICION DE FUNCIONES ----------------------------------------
# ------------------------------------------------------------------
#


# ------------------------------------------------------------------
# Percepción
# ------------------------------------------------------------------
from enum import Enum


def a(): ...


# ------------------------------------------------------------------
# Movimiento
# ------------------------------------------------------------------


# ------------------------------------------------------------------
# Interacción con entidades
# ------------------------------------------------------------------


# ------------------------------------------------------------------
# Comunicación
# ------------------------------------------------------------------


# ------------------------------------------------------------------
# Reproducción
# ------------------------------------------------------------------
#
#
class ACCIONES_ENUM(Enum):
    observe = "observe"
    move = "move"


ACCIONES: dict[str, dict] = {
    # ------------------------------------------------------------------
    # Percepción
    # ------------------------------------------------------------------
    "observe": {
        "coste": 1,
        "descripcion": "Raycast en abanico. Payload: center_angle(f) + fov(f) + num_rays(i).",
        "funcion": a,
    },
    # ------------------------------------------------------------------
    # Movimiento
    # ------------------------------------------------------------------
    "move": {
        "coste": 2,
        "descripcion": "Mover el bot. Payload: dx(f) + dy(f) en casillas.",
        "funcion": a,
    },
    "rotate": {
        "coste": 2,
        "descripcion": "Rotar el bot. Payload: angle(f) en radianes (absoluto).",
        "funcion": a,
    },
    # ------------------------------------------------------------------
    # Interacción con entidades
    # ------------------------------------------------------------------
    "interact": {
        "coste": 3,
        "descripcion": "Interacción genérica (atacar, recoger...). Payload: JSON con kind+target_id+data.",
        "funcion": a,
    },
    # ------------------------------------------------------------------
    # Comunicación
    # ------------------------------------------------------------------
    "broadcast": {
        "coste": 2,
        "descripcion": "Emitir mensaje a bots cercanos. Payload: radius(i) + message(bytes).",
        "funcion": a,
    },
    # ------------------------------------------------------------------
    # Reproducción
    # ------------------------------------------------------------------
    "reproduce": {
        "coste": 5,
        "descripcion": "Solicitar reproducción asexual. El Mundo decide si se aprueba.",
        "funcion": a,
    },
}

# ---------------------------------------------------------------------------
# Helpers — usados por hypervisor.py y cualquier otro módulo que los necesite
# ---------------------------------------------------------------------------


def get_coste(action_name: str) -> int:
    """
    Devuelve el coste en puntos de una acción.
    Si la acción no existe devuelve 0 (el Hypervisor dejará pasar
    y será el Mundo quien rechace si no la conoce).
    """
    entrada = ACCIONES.get(action_name)
    return entrada["coste"] if entrada else 0


def accion_conocida(action_name: str) -> bool:
    """True si la acción está registrada en este fichero."""
    return action_name in ACCIONES


def listar() -> list[str]:
    """Lista de nombres de acciones registradas."""
    return list(ACCIONES.keys())
