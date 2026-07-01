"""
Gestores/Bots/Gestor_Bots/acciones_delegadas.py

Registro de acciones que los Hypervisores ejecutan localmente
en lugar de reenviar al Mundo.

Reglas:
  - Solo acciones que NO tienen efecto en el estado del Mundo.
  - De momento: acciones de obtención de información (observe, ...).
  - El Mundo no sabe qué acciones están aquí; este fichero es
    exclusivo del Gestor_Bots.

Para añadir una acción delegada:
  1. Asegúrate de que su "funcion" en api_acciones.py acepta HVContext.
  2. Añádela a ACCIONES_DELEGADAS.

Para quitarla: elimínala de la lista. Sin más cambios.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Lista de callables delegadas al HV
# ---------------------------------------------------------------------------
# Lista de nombres de acciones que el HV intercepta y ejecuta localmente.
# La función se obtiene en tiempo de ejecución desde ACCIONES.

ACCIONES_DELEGADAS: list[str] = [
    "mirar",
]
