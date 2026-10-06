# Infraestructura/Gestores/Consola/accion_consola.py
"""
accion_consola.py — Descripción de una acción invocable desde la
consola: nombre por el que se escribe, cuestionario de campos que
necesita, y el handler que la ejecuta de verdad.

No confundir con ComandoConsolaRequest (gestor_mundo_service.proto):
aquello es el transporte de red hacia Gestor_Mundo para un tipo de
comando concreto; esto es la capa de CLI que decide qué preguntar al
usuario y qué método de ComunicacionesLocal llamar como consecuencia
— una AccionConsola puede llamar a cualquier método de
ComunicacionesLocal, viaje o no por ComandoConsolaRequest por dentro.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Awaitable, Callable

from Infraestructura.Gestores.Consola.cuestionario import CampoCuestionario

HandlerAccion = Callable[..., Awaitable[str]]


@dataclass
class AccionConsola:
    num: int
    nombre: str
    descripcion: str
    handler: HandlerAccion
    campos: list[CampoCuestionario] = field(default_factory=list)