# Infraestructura/Gestores/Mundo/Logica_Mundo/logica_mundo.py
"""
logica_mundo.py — Lógica pura de Logica_Mundo.

Única fuente de verdad de:
  - Estado gold (celdas + elementos + posiciones de bots).
  - Identidad: asignación de IDs nuevos para elementos.
  - Eventos globales (spawn/despawn/consulta).
  - Elementos globales de mundo (ciclo día-noche, ciclo lunar, etc.):
    son estado ("qué existe y qué significa"), por eso viven aquí y no
    en Gestor_Mundo, aunque avancen una vez por tick.
  - Resolución de acciones de bots (mirar, interact, etc.) vía ACCIONES.
  - Resolución de consultas de representación (Vista_Foco / Unity),
    con recorte por región y filtro por comportamiento.

Traducción con el transporte (common.Cell):
  Un Cell proto tiene 3 slots de bytes (suelo/bot/resto), cada uno la
  serialización JSON de Elemento.serializar(). Internamente, esta clase
  guarda solo IDs en Celda (suelo/bot/resto) y los objetos Elemento ya
  reconstruidos en self._elements — evita reserializar/deserializar en
  cada acceso; la traducción a bytes solo ocurre en la frontera de red
  (_cell_a_celda / _celda_a_cell).

Gestor_Mundo ya NO mantiene estado de mundo propio: le pide aquí lo que
necesita para construir ghost zones y le entrega aquí los deltas de cada
tick para que esta clase los consolide (ver ObtenerCeldasEnRegion /
ActualizarCeldas en el proto). También le pide, una vez por tick, que
avance los elementos globales.

Variables de entorno relevantes:
  SNAPSHOT_DIR
"""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from Core.Entities.Elementos.registry import reconstruir_elemento
from Infraestructura.Gestores.tipos_comunes import ActionResult

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
#  Tipos internos
# ─────────────────────────────────────────────────────────────


@dataclass
class Celda:
    """
    Contenido de una celda del grid, en memoria.

    suelo / bot / resto son IDs (claves de `_elements`), NUNCA los
    objetos ni los bytes serializados — esos viven en self._elements
    (una única copia) y se traducen a bytes solo al cruzar la frontera
    de red (ver _celda_a_cell).
    """

    suelo: Optional[int] = None
    bot: Optional[int] = None
    resto: list[int] = field(default_factory=list)


@dataclass
class GlobalEvent:
    """Evento global activo (afecta a todos los sectores)."""

    event_id: str
    type: str
    pos: Optional[tuple[int, int]]  # None si el evento no tiene posición
    payload: bytes


class ElementoGlobal:
    """
    Clase base para elementos globales de mundo (ciclo día-noche, ciclo
    lunar, etc.). Migrada desde gestor_mundo.py: es estado del mundo
    ("qué existe"), no mecánica de tick ("cuándo se computa").
    """

    def tick(self, tick_id: int) -> dict:
        """Avanza el estado un tick. Devuelve dict con cambios para sectores."""
        raise NotImplementedError

    def to_snapshot(self) -> dict:
        raise NotImplementedError

    @classmethod
    def from_snapshot(cls, data: dict) -> "ElementoGlobal":
        raise NotImplementedError


# ─────────────────────────────────────────────────────────────
#  LogicaMundo
# ─────────────────────────────────────────────────────────────


class LogicaMundo:

    def __init__(self):
        # ─────────────────────────────────────────────────────
        #  Configuración desde entorno
        # ─────────────────────────────────────────────────────
        self.SNAPSHOT_DIR = Path(os.getenv("SNAPSHOT_DIR", "/data/snapshots_logica"))

        # Estado gold — Celda guarda IDs, self._elements guarda objetos.
        self._gold_cells: dict[tuple[int, int], Celda] = {}

        # id → objeto Elemento ya reconstruido (incluye bots).
        self._elements: dict[int, Any] = {}

        # bot_id → posición (fuente de verdad exclusiva).
        self._bot_positions: dict[str, tuple[int, int]] = {}

        # Contador de IDs de elemento. Empieza en 1 para que 0 pueda
        # seguir usándose como "sin elemento" en los campos de Celda.
        self._id_counter: int = 0

        # Eventos globales activos, indexados por event_id.
        self._active_events: dict[str, GlobalEvent] = {}
        self._event_counter: int = 0

        # Elementos globales de mundo (ciclo día-noche, ciclo lunar...).
        self._elementos_globales: dict[str, ElementoGlobal] = {
            # Añadir más elementos globales aquí
        }

        # Lock único para todas las operaciones que tocan el estado gold.
        # Se mantiene deliberadamente ligero (dict lookups + serialización
        # JSON, sin I/O de red ni de disco) para no convertirse en cuello
        # de botella al crecer el número de bots.
        self._lock: asyncio.Lock = asyncio.Lock()

        logger.info("LogicaMundo inicializado.")

    # ─────────────────────────────────────────────────────────
    #  Traducción Cell (proto) ↔ Celda (interno)
    # ─────────────────────────────────────────────────────────

    def _slot_bytes_a_id(self, blob: bytes) -> Optional[int]:
        """
        Deserializa un slot de Cell (bytes JSON, o vacío) a un ID,
        registrando/actualizando el objeto reconstruido en self._elements.

        Debe llamarse con self._lock ya adquirido.
        """
        if not blob:
            return None

        data = json.loads(blob.decode())
        elemento = reconstruir_elemento(data)

        eid = getattr(elemento, "id", None)
        if eid is None:
            raise ValueError(
                f"Elemento deserializado sin 'id' (clase={data.get('__clase__')!r})."
            )

        self._elements[eid] = elemento
        return eid

    def _id_a_slot_bytes(self, eid: Optional[int]) -> bytes:
        """
        Serializa el elemento referenciado por `eid` a bytes JSON, o
        b"" si el slot está vacío. Debe llamarse con self._lock adquirido.
        """
        if eid is None:
            return b""
        elemento = self._elements.get(eid)
        if elemento is None:
            logger.warning("_id_a_slot_bytes: elemento %s no encontrado.", eid)
            return b""
        return json.dumps(elemento.serializar()).encode()

    def _cell_a_celda(self, cell) -> Celda:
        """
        Traduce un common.Cell (proto, bytes por slot) a Celda (IDs).
        Debe llamarse con self._lock adquirido.
        """
        return Celda(
            suelo=self._slot_bytes_a_id(cell.suelo),
            bot=self._slot_bytes_a_id(cell.bot),
            resto=[
                eid
                for eid in (self._slot_bytes_a_id(blob) for blob in cell.resto)
                if eid is not None
            ],
        )

    def _celda_a_cell(self, pos: tuple[int, int], celda: Celda):
        """
        Traduce una Celda (IDs) a common.Cell (proto, bytes por slot).
        Import diferido para no acoplar logica_mundo.py a los stubs
        generados si se usa en un contexto sin ellos disponibles.
        Debe llamarse con self._lock adquirido.
        """
        from Infraestructura.Gestores.Transporte.Proto_Generated import (
            common_pb2 as common_pb,
        )

        x, y = pos
        return common_pb.Cell(
            pos=common_pb.Position(x=x, y=y),
            suelo=self._id_a_slot_bytes(celda.suelo),
            bot=self._id_a_slot_bytes(celda.bot),
            resto=[self._id_a_slot_bytes(eid) for eid in celda.resto],
        )

    # ─────────────────────────────────────────────────────────
    #  Identidad
    # ─────────────────────────────────────────────────────────

    async def asignar_id(self) -> int:
        """Genera un ID nuevo y único para un elemento."""
        async with self._lock:
            self._id_counter += 1
            return self._id_counter

    # ─────────────────────────────────────────────────────────
    #  Elementos — alta / edición / baja
    # ─────────────────────────────────────────────────────────

    async def crear_elemento(
        self, pos: tuple[int, int], type_id: str, element: bytes
    ) -> tuple[bool, str]:
        """
        Registra un elemento nuevo en la posición indicada.

        `element` llega ya serializado (bytes JSON, con su ID incluido
        — asignado previamente vía asignar_id() por quien construyó el
        objeto). Aquí se deserializa y se indexa.
        """
        async with self._lock:
            try:
                eid = self._slot_bytes_a_id(element)
            except (ValueError, json.JSONDecodeError) as exc:
                return False, f"Elemento inválido: {exc}"

            if eid is None:
                return False, "El elemento no tiene 'id' asignado."

            celda = self._gold_cells.setdefault(pos, Celda())
            # type_id decide en qué slot se coloca — misma convención
            # que ya usaba mirar.py (suelo/bot/resto).
            if type_id == "suelo":
                celda.suelo = eid
            elif type_id == "bot":
                celda.bot = eid
                self._bot_positions[str(eid)] = pos
            else:
                celda.resto.append(eid)

            logger.debug("Elemento %s creado en %s (type_id=%s)", eid, pos, type_id)
            return True, ""

    async def modificar_elemento(
        self, pos: tuple[int, int], type_id: str, patch: dict
    ) -> tuple[bool, str]:
        """
        Aplica un patch (dict de atributo → nuevo valor) al elemento de
        `type_id` presente en `pos`. No decide semántica de cada
        atributo — delega en el propio objeto Elemento.
        """
        async with self._lock:
            celda = self._gold_cells.get(pos)
            if celda is None:
                return False, f"No hay celda en {pos}."

            eid = {"suelo": celda.suelo, "bot": celda.bot}.get(type_id)
            if eid is None:
                return False, f"No hay elemento de tipo '{type_id}' en {pos}."

            elemento = self._elements.get(eid)
            if elemento is None:
                return False, f"Elemento {eid} no encontrado en _elements."

            for attr, valor in patch.items():
                setattr(elemento, attr, valor)

            return True, ""

    async def eliminar_elemento(
        self, pos: tuple[int, int], type_id: str
    ) -> tuple[bool, str]:
        async with self._lock:
            celda = self._gold_cells.get(pos)
            if celda is None:
                return False, f"No hay celda en {pos}."

            if type_id == "suelo":
                eid, celda.suelo = celda.suelo, None
            elif type_id == "bot":
                eid, celda.bot = celda.bot, None
                if eid is not None:
                    self._bot_positions.pop(str(eid), None)
            else:
                return False, f"Tipo de eliminación no soportado: '{type_id}'."

            if eid is not None:
                self._elements.pop(eid, None)

            # Limpiar la celda del dict si quedó vacía — evita que
            # _gold_cells crezca indefinidamente con celdas fantasma.
            if celda.suelo is None and celda.bot is None and not celda.resto:
                self._gold_cells.pop(pos, None)

            return True, ""

    # ─────────────────────────────────────────────────────────
    #  Acciones de bots
    # ─────────────────────────────────────────────────────────

    async def resolver_accion(
        self, bot_id: str, action_type: str, payload: bytes
    ) -> ActionResult:
        """
        Resuelve una acción de un bot contra ACCIONES (api_acciones.py).
        Todo el estado (gold_cells/elements/bot_positions) vive en este
        mismo proceso — sin red de por medio para leerlo, que era el
        objetivo de mover esta lógica aquí.
        """
        from Infraestructura.Gestores.Mundo.Logica_Mundo.api_acciones import (
            ACCIONES,
            AccionContext,
        )

        entrada = ACCIONES.get(action_type)
        if entrada is None:
            logger.warning(
                "resolver_accion: acción desconocida '%s' (bot %s)", action_type, bot_id
            )
            return ActionResult(ok=False, error=f"Acción desconocida: {action_type}")

        fn = entrada.get("funcion")
        if fn is None:
            logger.warning(
                "resolver_accion: acción '%s' no tiene funcion (bot %s)",
                action_type,
                bot_id,
            )
            return ActionResult(
                ok=False,
                error=f"Acción '{action_type}' no ejecutable por Logica_Mundo.",
            )

        ctx = AccionContext(
            bot_id=bot_id,
            payload=payload,
            gold_cells=self._gold_cells,
            elements=self._elements,
            bot_positions=self._bot_positions,
        )

        try:
            async with self._lock:
                return await fn(ctx)
        except Exception as exc:
            logger.error(
                "Error en resolver_accion '%s' para bot %s: %s",
                action_type,
                bot_id,
                exc,
            )
            return ActionResult(ok=False, error=str(exc))

    # ─────────────────────────────────────────────────────────
    #  Eventos globales
    # ─────────────────────────────────────────────────────────

    async def spawn_global_event(
        self, type_: str, pos: Optional[tuple[int, int]], payload: bytes
    ) -> tuple[bool, str, str]:
        async with self._lock:
            self._event_counter += 1
            event_id = f"evt_{self._event_counter:06d}"
            self._active_events[event_id] = GlobalEvent(
                event_id=event_id, type=type_, pos=pos, payload=payload
            )
            logger.info("Evento global '%s' creado (%s)", event_id, type_)
            return True, "", event_id

    async def despawn_global_event(
        self, event_id: str, reason: str
    ) -> tuple[bool, str]:
        async with self._lock:
            if event_id not in self._active_events:
                return False, f"Evento '{event_id}' no encontrado."
            del self._active_events[event_id]
            logger.info("Evento global '%s' finalizado (%s)", event_id, reason)
            return True, ""

    async def get_active_events(self) -> list[GlobalEvent]:
        async with self._lock:
            return list(self._active_events.values())

    # ─────────────────────────────────────────────────────────
    #  Elementos globales de mundo (ciclo día-noche, lunar...)
    # ─────────────────────────────────────────────────────────

    async def avanzar_elementos_globales(self, tick_id: int) -> dict:
        """
        Avanza un tick todos los elementos globales registrados y
        devuelve el conjunto de cambios acumulados. Llamado por
        Gestor_Mundo una vez por tick.
        """
        cambios: dict = {}
        async with self._lock:
            for elem in self._elementos_globales.values():
                cambios.update(elem.tick(tick_id))
        return cambios

    # ─────────────────────────────────────────────────────────
    #  Soporte al ciclo de tick de Gestor_Mundo
    # ─────────────────────────────────────────────────────────

    async def obtener_celdas_en_region(
        self,
        min_pos: tuple[int, int],
        max_pos: tuple[int, int],
        excluir_min: Optional[tuple[int, int]] = None,
        excluir_max: Optional[tuple[int, int]] = None,
    ) -> list:
        """
        Devuelve una lista de common.Cell (proto) con las celdas dentro
        de [min_pos, max_pos), opcionalmente excluyendo el rectángulo
        [excluir_min, excluir_max).

        Usado por Gestor_Mundo para ghost zones (excluir = sector propio)
        y carga inicial de sector (sin exclusión).
        """
        x0, y0 = min_pos
        x1, y1 = max_pos

        tiene_exclusion = excluir_min is not None and excluir_max is not None
        if tiene_exclusion:
            ex0, ey0 = excluir_min
            ex1, ey1 = excluir_max

        async with self._lock:
            resultado = []
            for (x, y), celda in self._gold_cells.items():
                if not (x0 <= x < x1 and y0 <= y < y1):
                    continue
                if tiene_exclusion and (ex0 <= x < ex1 and ey0 <= y < ey1):
                    continue
                resultado.append(self._celda_a_cell((x, y), celda))
            return resultado

    async def actualizar_celdas(self, changed_cells: list) -> None:
        """
        Aplica los cambios consolidados por Gestor_Mundo tras _fase_2.

        `changed_cells` es una lista de common.Cell (proto) tal como
        llegan de Sector.GetDelta. Una Cell con los 3 slots vacíos
        (suelo=b"", bot=b"", resto=[]) indica que la posición quedó
        vacía y se elimina de _gold_cells.
        """
        async with self._lock:
            for cell in changed_cells:
                pos = (cell.pos.x, cell.pos.y)
                celda = self._cell_a_celda(cell)
                if celda.suelo is None and celda.bot is None and not celda.resto:
                    self._gold_cells.pop(pos, None)
                else:
                    self._gold_cells[pos] = celda

    # ─────────────────────────────────────────────────────────
    #  Representación (Vista_Foco / Unity)
    # ─────────────────────────────────────────────────────────

    async def consultar_representacion(
        self,
        min_pos: tuple[int, int],
        max_pos: tuple[int, int],
        incluir: list[str],
        modo: str,
    ) -> bytes:
        """
        Resuelve una consulta de representación con recorte por región
        y filtro por comportamiento — todo en este proceso, para que
        solo cruce la red el resultado ya reducido.

        `incluir` es una lista de nombres de comportamiento (p.ej.
        ["Color", "Bot"]) resuelta de forma genérica contra
        elemento.get_comportamiento(nombre) — composable, sin una
        función por vista.

        NOTA: el formato de serialización devuelto (JSON aquí como
        placeholder) queda pendiente de cerrar con vision_unity.py.
        """
        x0, y0 = min_pos
        x1, y1 = max_pos

        resultado = []
        async with self._lock:
            for (x, y), celda in self._gold_cells.items():
                if not (x0 <= x < x1 and y0 <= y < y1):
                    continue

                ids = [celda.suelo, celda.bot, *celda.resto]
                for eid in ids:
                    if eid is None:
                        continue
                    elemento = self._elements.get(eid)
                    if elemento is None:
                        continue

                    comportamientos_encontrados = {}
                    for nombre in incluir:
                        comp = elemento.get_comportamiento(nombre)
                        if comp is not None:
                            comportamientos_encontrados[nombre] = comp

                    if not comportamientos_encontrados:
                        continue

                    resultado.append(
                        {
                            "id": eid,
                            "x": x,
                            "y": y,
                            "comportamientos": {
                                nombre: str(valor)
                                for nombre, valor in comportamientos_encontrados.items()
                            },
                        }
                    )

        return json.dumps({"modo": modo, "elementos": resultado}).encode()

    # ─────────────────────────────────────────────────────────
    #  Persistencia
    # ─────────────────────────────────────────────────────────

    async def save_snapshot(self, snapshot_id: str) -> None:
        """
        Guarda el estado gold (celdas + elementos + IDs + eventos +
        elementos globales) a disco. Los elementos se serializan con
        Elemento.serializar() — ya no hace falta un TODO de "guardar el
        proto en crudo", el registry permite reconstruirlos de verdad.
        """
        self.SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        path = self.SNAPSHOT_DIR / f"logica_mundo_{snapshot_id}.json"

        async with self._lock:
            data = {
                "snapshot_id": snapshot_id,
                "fecha": datetime.datetime.now().isoformat(),
                "id_counter": self._id_counter,
                "gold_cells": {
                    f"{x},{y}": {
                        "suelo": celda.suelo,
                        "bot": celda.bot,
                        "resto": celda.resto,
                    }
                    for (x, y), celda in self._gold_cells.items()
                },
                "elements": {
                    str(eid): elemento.serializar()
                    for eid, elemento in self._elements.items()
                },
                "bot_positions": {
                    bid: list(pos) for bid, pos in self._bot_positions.items()
                },
                "active_events": {
                    eid: {
                        "type": ev.type,
                        "pos": list(ev.pos) if ev.pos else None,
                        "payload": ev.payload.hex(),
                    }
                    for eid, ev in self._active_events.items()
                },
                "elementos_globales": {
                    nombre: elem.to_snapshot()
                    for nombre, elem in self._elementos_globales.items()
                },
            }

        path.write_text(json.dumps(data))
        logger.info("Snapshot de Logica_Mundo guardado: %s", path)

    async def load_state(self, snapshot_id: str) -> None:
        path = self.SNAPSHOT_DIR / f"logica_mundo_{snapshot_id}.json"
        if not path.exists():
            logger.warning("Snapshot '%s' no encontrado en %s.", snapshot_id, path)
            return

        data = json.loads(path.read_text())

        async with self._lock:
            self._id_counter = data.get("id_counter", 0)

            # Reconstruir elementos ANTES que gold_cells, porque
            # gold_cells solo referencia IDs que deben existir ya en
            # _elements.
            self._elements = {
                int(eid): reconstruir_elemento(edata)
                for eid, edata in data.get("elements", {}).items()
            }

            self._gold_cells = {
                tuple(map(int, k.split(","))): Celda(
                    suelo=v["suelo"], bot=v["bot"], resto=v["resto"]
                )
                for k, v in data.get("gold_cells", {}).items()
            }

            self._bot_positions = {
                bid: tuple(pos) for bid, pos in data.get("bot_positions", {}).items()
            }

            self._active_events = {
                eid: GlobalEvent(
                    event_id=eid,
                    type=ev["type"],
                    pos=tuple(ev["pos"]) if ev["pos"] else None,
                    payload=bytes.fromhex(ev["payload"]),
                )
                for eid, ev in data.get("active_events", {}).items()
            }

            eg_data = data.get("elementos_globales", {})
            for nombre, elem in self._elementos_globales.items():
                if nombre in eg_data:
                    elem.__dict__.update(elem.from_snapshot(eg_data[nombre]).__dict__)

        logger.info("Estado de Logica_Mundo restaurado desde %s", path)
