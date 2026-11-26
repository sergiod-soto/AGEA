# Infraestructura/Gestores/Mundo/Hidrologia/modelos.py
"""
modelos.py - Estructuras de datos para el subsistema hidrográfico desacoplado.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DatosAtmosferaHidro:
    """Condiciones atmosféricas agregadas por celda de atmósfera."""

    pos_clima: tuple[int, int]
    precipitacion_kg_m2: float = 0.0
    temperatura_aire: float = 293.15  # K
    temperatura_suelo: float = 293.15  # K
    humedad_absoluta: float = 0.005  # kg/m3
    viento_intensidad: float = 0.0  # m/s


@dataclass
class CeldaInundable:
    """Información de una celda de cuenca lacustre o ensanchamiento."""

    pos: tuple[int, int]
    elev: float
    inundada: bool = False
    suelo_original: str = "Suelo_Tierra"


@dataclass
class ResultadoTickHidro:
    """
    Resultado del avance de un tick hidrográfico (Fase 1).
    Contiene las mutaciones discretas de terreno para aplicar en Fase 2,
    así como estadísticas y eventos generados.
    """

    tick_id: int
    changed_cells: list[dict] = field(default_factory=list)
    caudal_vertido_mar: float = 0.0
    lagos_desbordando: list[int] = field(default_factory=list)
    rios_activos: list[int] = field(default_factory=list)
    volumen_total_almacenado: float = 0.0
    eventos: list[dict] = field(default_factory=list)
