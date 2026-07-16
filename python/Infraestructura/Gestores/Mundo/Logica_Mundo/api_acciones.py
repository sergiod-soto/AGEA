# Infraestructura/Gestores/Mundo/Logica_Mundo/api_acciones.py
from __future__ import annotations
from dataclasses import dataclass
from Infraestructura.Gestores.Mundo.Logica_Mundo.Acciones.mirar import mirar


@dataclass
class AccionContext:
    bot_id: str
    payload: bytes
    gold_cells: dict | None = None
    elements: dict | None = None
    bot_positions: dict | None = None


ACCIONES: dict[str, dict] = {
    "mirar": {
        "coste": 1,
        "descripcion": "Lanza un rayo...",
        "funcion": mirar,
    },
}


def get_coste(action_name: str) -> int:
    entrada = ACCIONES.get(action_name)
    return entrada["coste"] if entrada else 0


def accion_conocida(action_name: str) -> bool:
    return action_name in ACCIONES


def listar() -> list[str]:
    return list(ACCIONES.keys())
