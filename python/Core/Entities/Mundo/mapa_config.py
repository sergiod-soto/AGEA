"""
Core/Mundo/mapa_config.py

Definición del objeto mapa que se pasa al Gestor_Mundo al arrancar.
Contiene todo lo necesario para que el Gestor_Mundo se auto-gestione:
dividir en sectores, distribuir datos estáticos y capas dinámicas,
y conocer las zonas de spawn iniciales.

El Gestor_Mundo es el único consumidor de este objeto.
Los sectores reciben únicamente el fragmento que les corresponde.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

MAX_SOUND_DISTANCE = 50

# ---------------------------------------------------------------------------
# Zona de spawn
# ---------------------------------------------------------------------------


@dataclass
class ZonaSpawn:
    """
    Región rectangular donde los bots pueden spawnear inicialmente.

    peso : probabilidad relativa respecto a otras zonas definidas.
           El Mundo normaliza los pesos al calcular la distribución.
           Ejemplo: dos zonas con peso 1.0 y 2.0 → 33% / 66%.
    """

    x_start: int
    y_start: int
    x_end: int
    y_end: int
    peso: float = 1.0

    def contiene(self, x: int, y: int) -> bool:
        return self.x_start <= x < self.x_end and self.y_start <= y < self.y_end

    def area(self) -> int:
        return (self.x_end - self.x_start) * (self.y_end - self.y_start)


# ---------------------------------------------------------------------------
# Capa dinámica (noise image)
# ---------------------------------------------------------------------------


@dataclass
class CapaDinamica:
    """
    Capa de valores continuos que cubre todo el grid y se actualiza
    cada cierto número de ticks (temperatura, humedad, etc.).

    nombre          : identificador usado por los sectores ("temperatura", ...)
    datos           : array numpy shape (grid_height, grid_width), dtype float32
    actualizar_cada : ticks entre cada recálculo global
    """

    nombre: str
    datos: np.ndarray  # shape (H, W), float32
    actualizar_cada: int = 10  # ticks

    def fragmento(
        self, x_start: int, y_start: int, x_end: int, y_end: int
    ) -> np.ndarray:
        """Devuelve el fragmento correspondiente a una región de sector."""
        return self.datos[y_start:y_end, x_start:x_end].copy()


# ---------------------------------------------------------------------------
# Objeto mapa principal
# ---------------------------------------------------------------------------


@dataclass
class MapaConfig:
    """
    Descripción completa del mapa. Se construye antes de arrancar la partida
    y se pasa al Gestor_Mundo una única vez.

    Parámetros
    ----------
    grid_width, grid_height : dimensiones totales en celdas.

    terrain_grid : array numpy shape (grid_height, grid_width), dtype int16.
        Cada valor es un tipo de tile (definido en Core/Entities/Elementos/
        Simples/Terreno). Inmutable durante la partida.

    elementos_estaticos : lista de elementos que no fuerzan carga de sector
        (Piedra, Arbol, Agua, Recipiente...) con su posición (x, y) ya
        asignada. El Gestor_Mundo los distribuye a los sectores al arrancar.

    capas_dinamicas : diccionario nombre → CapaDinamica. Calculadas
        centralmente y distribuidas a sectores activos/dormidos cada
        CapaDinamica.actualizar_cada ticks.

    zonas_spawn : regiones donde spawnean los bots en la fase inicial.
        Los pesos se normalizan automáticamente.

    sector_size : celdas por lado de cada sector. Único parámetro que
        controla la partición. El número de sectores se deriva:
            cols = ceil(grid_width  / sector_size)
            rows = ceil(grid_height / sector_size)
    """

    # ── Dimensiones ───────────────────────────────────────────────────────
    grid_width: int
    grid_height: int

    # ── Terreno estático ──────────────────────────────────────────────────
    terrain_grid: np.ndarray  # shape (H, W), int16, inmutable
    elementos_estaticos: list[Any] = field(default_factory=list)
    # Any = instancias de elementos sin FuerzaCargaSector con atributos x, y

    # ── Capas dinámicas ───────────────────────────────────────────────────
    capas_dinamicas: dict[str, CapaDinamica] = field(default_factory=dict)

    # ── Zonas de spawn ────────────────────────────────────────────────────
    zonas_spawn: list[ZonaSpawn] = field(default_factory=list)

    # ── Partición ─────────────────────────────────────────────────────────
    sector_size: int = 100

    # ------------------------------------------------------------------
    # Propiedades derivadas
    # ------------------------------------------------------------------

    @property
    def sector_cols(self) -> int:
        """Número de sectores en X."""
        import math

        return math.ceil(self.grid_width / self.sector_size)

    @property
    def sector_rows(self) -> int:
        """Número de sectores en Y."""
        import math

        return math.ceil(self.grid_height / self.sector_size)

    @property
    def num_sectores(self) -> int:
        return self.sector_cols * self.sector_rows

    # ------------------------------------------------------------------
    # Helpers para el Gestor_Mundo
    # ------------------------------------------------------------------

    def region_de_sector(self, col: int, row: int) -> tuple[int, int, int, int]:
        """
        Devuelve (x_start, y_start, x_end, y_end) del sector (col, row).
        x_end / y_end están acotados al tamaño real del grid (último sector
        puede ser más pequeño si el grid no es múltiplo de sector_size).
        """
        x_start = col * self.sector_size
        y_start = row * self.sector_size
        x_end = min(x_start + self.sector_size, self.grid_width)
        y_end = min(y_start + self.sector_size, self.grid_height)
        return x_start, y_start, x_end, y_end

    def terrain_de_sector(self, col: int, row: int) -> np.ndarray:
        """Fragmento del terrain_grid correspondiente al sector (col, row)."""
        x0, y0, x1, y1 = self.region_de_sector(col, row)
        return self.terrain_grid[y0:y1, x0:x1].copy()

    def elementos_de_sector(self, col: int, row: int) -> list[Any]:
        """Elementos estáticos que caen dentro del sector (col, row)."""
        x0, y0, x1, y1 = self.region_de_sector(col, row)
        return [
            e for e in self.elementos_estaticos if x0 <= e.x < x1 and y0 <= e.y < y1
        ]

    def capas_de_sector(self, col: int, row: int) -> dict[str, np.ndarray]:
        """Fragmentos de capas dinámicas para el sector (col, row)."""
        x0, y0, x1, y1 = self.region_de_sector(col, row)
        return {
            nombre: capa.fragmento(x0, y0, x1, y1)
            for nombre, capa in self.capas_dinamicas.items()
        }

    def sector_de_coordenada(self, x: int, y: int) -> tuple[int, int]:
        """Dado un punto (x, y) devuelve el (col, row) del sector que lo contiene."""
        return x // self.sector_size, y // self.sector_size

    def validar(self) -> None:
        """
        Comprueba consistencia básica del mapa.
        Lanzar antes de pasar el objeto al Gestor_Mundo.
        """
        assert self.grid_width > 0, "grid_width debe ser > 0"
        assert self.grid_height > 0, "grid_height debe ser > 0"
        assert self.sector_size > 0, "sector_size debe ser > 0"

        assert self.terrain_grid.shape == (self.grid_height, self.grid_width), (
            f"terrain_grid shape {self.terrain_grid.shape} no coincide "
            f"con ({self.grid_height}, {self.grid_width})"
        )

        for nombre, capa in self.capas_dinamicas.items():
            assert capa.datos.shape == (self.grid_height, self.grid_width), (
                f"Capa '{nombre}' shape {capa.datos.shape} no coincide " f"con el grid"
            )
            assert (
                capa.actualizar_cada > 0
            ), f"Capa '{nombre}': actualizar_cada debe ser > 0"

        for zona in self.zonas_spawn:
            assert (
                0 <= zona.x_start < zona.x_end <= self.grid_width
            ), f"ZonaSpawn X fuera de rango: {zona}"
            assert (
                0 <= zona.y_start < zona.y_end <= self.grid_height
            ), f"ZonaSpawn Y fuera de rango: {zona}"
            assert zona.peso > 0, f"ZonaSpawn peso debe ser > 0: {zona}"
