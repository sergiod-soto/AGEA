"""
sector.py
---------
Lógica principal de un sector del mundo.

Responsabilidades:
  - Mantener el estado de las celdas de su región en memoria (objetos deserializados)
  - Ejecutar el tick de computación (solo si ACTIVO)
  - Gestionar ghost zones recibidas del Gestor_Mundo
  - Procesar sonidos cross-border
  - Detectar y reportar migraciones de bots
  - Persistir su estado en S3 cuando recibe SaveSnapshot

La serialización/deserialización de elementos está desacoplada en CeldaStore.
Para cambiar la estrategia de almacenamiento, reimplementar CeldaStore sin
tocar este fichero.

Carpeta: Gestores/Mundo/Sector/

Variables de entorno:
  SECTOR_COL, SECTOR_ROW
  SECTOR_SIZE
  MAX_VISION_DISTANCE
  GESTOR_MUNDO_ADDRESS
  SECTOR_WORKERS
  S3_BUCKET, S3_PREFIX          (para snapshots)
"""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from numpy import int64

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  Configuración
# ─────────────────────────────────────────────

SECTOR_COL = int(os.getenv("SECTOR_COL", 0))
SECTOR_ROW = int(os.getenv("SECTOR_ROW", 0))
SECTOR_SIZE = int(os.getenv("SECTOR_SIZE", 100))
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_PREFIX = os.getenv("S3_PREFIX", "snapshots/sectores")


# ─────────────────────────────────────────────
#  Modo de sector
# ─────────────────────────────────────────────


class SectorMode(Enum):
    INACTIVO = 0
    DORMIDO = 1
    ACTIVO = 2


# ─────────────────────────────────────────────
#  CeldaStore
# ─────────────────────────────────────────────


class CeldaStore:
    """
    Almacén de celdas en memoria como objetos Python deserializados.

    Internamente: dict[(x, y), dict[int64, Elemento]]
    (Se accede con posicion → ID)


    La serialización proto ↔ objeto se delega al registry de elementos
    (a implementar en un script separado cuando el registry esté disponible).
    """

    def __init__(self):
        self._celdas: dict[tuple[int, int], dict[int64, Any]] = {}

    def get(self, x: int, y: int) -> Optional[Any]:
        return self._celdas.get((x, y))

    def set(
        self, x: int, y: int, elemento: dict[tuple[int, int], dict[int64, Any]]
    ) -> None:
        self._celdas[(x, y)] = elemento

    def delete(self, x: int, y: int) -> None:
        self._celdas.pop((x, y), None)

    def items(self):
        return self._celdas.items()

    def __contains__(self, key: tuple[int, int]) -> bool:
        return key in self._celdas

    def from_proto_cell(self, cell) -> None:
        """
        Deserializa una Cell proto y la almacena.
        TODO: usar el registry de elementos cuando esté disponible.
              Por ahora guarda el proto en crudo para no perder datos.
        """
        key = (cell.pos.x, cell.pos.y)
        self._celdas[key] = cell

    def to_proto_cells(self, proto_cell_class, proto_position_class) -> list:
        """
        Serializa todas las celdas a lista de Cell proto.
        TODO: usar el registry de elementos cuando esté disponible.
        """
        result = []
        for (x, y), elemento in self._celdas.items():
            if hasattr(elemento, "SerializeToString"):
                result.append(elemento)
            else:
                # TODO: elemento.to_proto() cuando el registry esté disponible
                pass
        return result

    def changed_since(
        self, tick_id: int, proto_cell_class, proto_position_class
    ) -> list:
        """
        Devuelve solo las celdas que cambiaron desde tick_id.
        TODO: implementar tracking de dirty cells por tick.
              Por ahora devuelve todas (conservador pero correcto).
        """
        return self.to_proto_cells(proto_cell_class, proto_position_class)


# ─────────────────────────────────────────────
#  Delta de tick
# ─────────────────────────────────────────────


@dataclass
class TickDelta:
    """Resultado de la computación de un tick."""

    tick_id: int
    changed_cells: list = field(default_factory=list)  # Cell proto
    outgoing_bots: list = field(default_factory=list)  # MigratingBot proto
    dead_bot_ids: list = field(default_factory=list)  # str
    emitted_sounds: list = field(default_factory=list)  # SoundEvent proto


# ─────────────────────────────────────────────
#  Sector
# ─────────────────────────────────────────────


class Sector:

    def __init__(self):
        # Siempre leer del entorno vivo para que los tests puedan
        # sobreescribir las variables antes de crear la instancia.
        # Fallback a los valores por defecto hardcodeados, no a las
        # constantes de módulo (que se fijan en el primer import).
        self._col = int(os.getenv("SECTOR_COL", "0"))
        self._row = int(os.getenv("SECTOR_ROW", "0"))
        self._size = int(os.getenv("SECTOR_SIZE", "100"))

        self._mode = SectorMode.INACTIVO

        # Celdas propias del sector
        self._celdas = CeldaStore()

        # Ghost zone: celdas de sectores vecinos dentro de MAX_VISION_DISTANCE
        self._ghost: dict[tuple[int, int], Any] = {}

        # Sonidos cross-border recibidos para el tick actual
        self._sounds_pendientes: list = []

        # Delta del último tick completado — listo para GetDelta
        self._last_delta: Optional[TickDelta] = None

        # tick_id del último tick recibido
        self._current_tick_id: int = -1

        # Bots presentes en este sector: bot_id → BotSnapshot proto
        self._bots: dict[str, Any] = {}

    # ─────────────────────────────────────────
    #  Propiedades de región (FIX principal)
    #  Derivadas de _col, _row, _size en lugar
    #  de las constantes globales de módulo.
    # ─────────────────────────────────────────

    @property
    def _x0(self) -> int:
        return self._col * self._size

    @property
    def _y0(self) -> int:
        return self._row * self._size

    @property
    def _x1(self) -> int:
        return self._x0 + self._size

    @property
    def _y1(self) -> int:
        return self._y0 + self._size

    # ─────────────────────────────────────────
    #  Ciclo de vida
    # ─────────────────────────────────────────

    def set_mode(self, mode: SectorMode) -> None:
        if self._mode == mode:
            return
        logger.info(
            "Sector (%d,%d): %s → %s", self._col, self._row, self._mode.name, mode.name
        )
        self._mode = mode

    def load_state(self, cells: list, bots: list) -> None:
        """
        Carga el estado gold enviado por Gestor_Mundo.
        Usado en arranque o tras recuperación de spot caído.
        """
        self._celdas = CeldaStore()
        for cell in cells:
            self._celdas.from_proto_cell(cell)

        self._bots = {bot.bot_id: bot for bot in bots}
        logger.info(
            "Sector (%d,%d): estado cargado — %d celdas, %d bots",
            self._col,
            self._row,
            len(list(self._celdas.items())),
            len(self._bots),
        )

    def get_state(self):
        """
        Devuelve el estado completo del sector (para GetState del servicer).
        """
        from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores.sector_service_pb2 import (
            Cell,
            Position,
            BotSnapshot,
        )

        cells = self._celdas.to_proto_cells(Cell, Position)
        bots = list(self._bots.values())
        return cells, bots

    # ─────────────────────────────────────────
    #  FASE 0 — Preparación del tick
    # ─────────────────────────────────────────

    def set_ghost_zone(self, tick_id: int, ghost_cells: list) -> None:
        """Recibe y almacena la ghost zone para este tick."""
        self._ghost = {}
        for cell in ghost_cells:
            key = (cell.pos.x, cell.pos.y)
            self._ghost[key] = cell
        logger.debug(
            "Sector (%d,%d): ghost zone cargada — %d celdas (tick %d)",
            self._col,
            self._row,
            len(self._ghost),
            tick_id,
        )

    def set_sounds(self, tick_id: int, sounds: list) -> None:
        """Recibe los sonidos cross-border para este tick."""
        self._sounds_pendientes = sounds
        logger.debug(
            "Sector (%d,%d): %d sonidos recibidos (tick %d)",
            self._col,
            self._row,
            len(sounds),
            tick_id,
        )

    def add_migrating_bot(self, tick_id: int, bot) -> None:
        """Registra un bot que acaba de migrar a este sector."""
        self._bots[bot.bot_id] = bot
        logger.debug(
            "Sector (%d,%d): bot %s migrado (tick %d)",
            self._col,
            self._row,
            bot.bot_id,
            tick_id,
        )

    # ─────────────────────────────────────────
    #  FASE 1 — Computación del tick
    # ─────────────────────────────────────────

    def compute_tick(self, tick_id: int) -> TickDelta:
        """
        Ejecuta la computación completa del tick.
        Solo llamado si el sector está en modo ACTIVO.
        """
        self._current_tick_id = tick_id
        delta = TickDelta(tick_id=tick_id)

        if self._mode != SectorMode.ACTIVO:
            self._last_delta = delta
            return delta

        self._procesar_sonidos(delta)
        self._tick_elementos(delta)
        self._detectar_migraciones(delta)

        self._sounds_pendientes = []

        self._last_delta = delta
        return delta

    def _procesar_sonidos(self, delta: TickDelta) -> None:
        """
        Aplica los efectos de los sonidos cross-border recibidos.
        TODO: implementar cuando la API de sonido esté definida.
        """
        for sound in self._sounds_pendientes:
            pass

    def _tick_elementos(self, delta: TickDelta) -> None:
        """
        Llama al tick de cada elemento activo en las celdas propias.
        TODO: implementar cuando los elementos tengan tick() definido.
        """
        # FIX: usar propiedades de instancia en lugar de constantes globales
        contexto_vision = _ContextoVision(
            celdas_propias=self._celdas,
            ghost=self._ghost,
            x0=self._x0,
            y0=self._y0,
            x1=self._x1,
            y1=self._y1,
        )

        for (x, y), elemento in list(self._celdas.items()):
            if not hasattr(elemento, "fuerza_sector_activo"):
                continue
            if not elemento.fuerza_sector_activo:
                continue
            # TODO: resultado = elemento.tick(contexto_vision)

    def _detectar_migraciones(self, delta: TickDelta) -> None:
        """
        Comprueba qué bots han salido de la región del sector
        y los añade a delta.outgoing_bots.
        """
        from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores.sector_service_pb2 import (
            MigratingBot,
            Position,
        )

        # FIX: usar propiedades de instancia en lugar de constantes globales
        x0, y0, x1, y1 = self._x0, self._y0, self._x1, self._y1

        bots_fuera = []
        for bot_id, bot in self._bots.items():
            x, y = bot.pos.x, bot.pos.y
            if not (x0 <= x < x1 and y0 <= y < y1):
                delta.outgoing_bots.append(
                    MigratingBot(
                        bot=bot,
                        target_pos=Position(x=x, y=y),
                    )
                )
                bots_fuera.append(bot_id)

        for bot_id in bots_fuera:
            del self._bots[bot_id]

    # ─────────────────────────────────────────
    #  FASE 2 — GetDelta
    # ─────────────────────────────────────────

    def get_delta(self, tick_id: int) -> Optional[TickDelta]:
        """
        Devuelve el delta del tick solicitado.
        Si tick_id no coincide con el último tick computado, devuelve None.
        """
        if self._last_delta is None or self._last_delta.tick_id != tick_id:
            logger.warning(
                "Sector (%d,%d): GetDelta tick_id=%d pero último tick=%s",
                self._col,
                self._row,
                tick_id,
                self._last_delta.tick_id if self._last_delta else "None",
            )
            return None
        return self._last_delta

    # ─────────────────────────────────────────
    #  Snapshot (S3)
    # ─────────────────────────────────────────

    async def save_snapshot(self, snapshot_id: str) -> None:
        """
        Persiste el estado del sector en S3 con el snapshot_id dado.
        TODO: implementar con aioboto3 cuando se decida el cliente AWS.
        """
        import json

        cells_raw = []
        for (x, y), elemento in self._celdas.items():
            cells_raw.append({"x": x, "y": y, "element": ""})

        bots_raw = []
        for bot_id, bot in self._bots.items():
            bots_raw.append({"bot_id": bot_id})

        data = {
            "snapshot_id": snapshot_id,
            "col": self._col,
            "row": self._row,
            "mode": self._mode.value,
            "tick_id": self._current_tick_id,
            "cells": cells_raw,
            "bots": bots_raw,
        }

        key = f"{S3_PREFIX}/sector_{self._col}_{self._row}/{snapshot_id}.json"

        logger.info(
            "TODO: snapshot sector (%d,%d) → s3://%s/%s (snapshot_id=%s)",
            self._col,
            self._row,
            S3_BUCKET,
            key,
            snapshot_id,
        )

    async def restore_snapshot(self, snapshot_id: str) -> None:
        """
        Restaura el estado del sector desde S3.
        TODO: implementar con aioboto3.
        """
        logger.info(
            "TODO: restore sector (%d,%d) desde s3://%s/%s/%s",
            self._col,
            self._row,
            S3_BUCKET,
            S3_PREFIX,
            snapshot_id,
        )


# ─────────────────────────────────────────────
#  ContextoVision
# ─────────────────────────────────────────────


@dataclass
class _ContextoVision:
    celdas_propias: CeldaStore
    ghost: dict
    x0: int
    y0: int
    x1: int
    y1: int

    def get_celda(self, x: int, y: int) -> Optional[Any]:
        if self.x0 <= x < self.x1 and self.y0 <= y < self.y1:
            return self.celdas_propias.get(x, y)
        return self.ghost.get((x, y))

    def en_region_propia(self, x: int, y: int) -> bool:
        return self.x0 <= x < self.x1 and self.y0 <= y < self.y1
