# Infraestructura/Gestores/Mundo/Logica_Mundo/logica_mundo.py
from __future__ import annotations

import asyncio
import datetime
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from numpy import uint64

from Core.Entities.Elementos.registry import reconstruir_elemento
from Infraestructura.Gestores.Transporte.gestor_bots_client_async import (
    GestorBotsClientAsync,
)
from Infraestructura.Gestores.tipos_comunes import ActionResult

logger = logging.getLogger(__name__)


@dataclass
class Celda:
    suelo: Optional[uint64] = None
    bot: Optional[uint64] = None
    resto: list[uint64] = field(default_factory=list)


@dataclass
class GlobalEvent:
    event_id: str
    type: str
    pos: Optional[tuple[int, int]]
    payload: bytes


class ElementoGlobal:
    def tick(self, tick_id: int) -> dict:
        """TODO: tick()"""
        raise NotImplementedError

    def to_snapshot(self) -> dict:
        """TODO: to_snapshot()"""
        raise NotImplementedError

    @classmethod
    def from_snapshot(cls, data: dict) -> "ElementoGlobal":
        """TODO: from_snapshot()"""
        raise NotImplementedError


class LogicaMundo:

    def __init__(self, gestor_bots_client: "GestorBotsClientAsync | None" = None):
        self.SNAPSHOT_DIR = Path(os.getenv("SNAPSHOT_DIR", "/data/snapshots_logica"))

        self._gold_cells: dict[tuple[int, int], Celda] = {}
        self._elements: dict[int, Any] = {}
        self._bot_positions: dict[str, tuple[int, int]] = {}
        self._id_counter: int = 0

        self._active_events: dict[str, GlobalEvent] = {}
        self._event_counter: int = 0

        self._elementos_globales: dict[str, ElementoGlobal] = {}

        self._gestor_bots_client = gestor_bots_client

        self._lock: asyncio.Lock = asyncio.Lock()

        logger.info("LogicaMundo inicializado.")

    # ---- Traducción Cell (proto) <-> Celda (interno) ----

    def _slot_bytes_a_id(self, blob: bytes) -> Optional[int]:
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
        if eid is None:
            return b""
        elemento = self._elements.get(eid)
        if elemento is None:
            logger.warning("_id_a_slot_bytes: elemento %s no encontrado.", eid)
            return b""
        return json.dumps(elemento.serializar()).encode()

    def _cell_a_celda(self, cell) -> Celda:
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

    # ---- Identidad ----

    async def asignar_id(self) -> int:
        async with self._lock:
            self._id_counter += 1
            return self._id_counter

    # ---- Elementos ----

    async def crear_elemento(
        self, pos: tuple[int, int], type_id: str, element: bytes
    ) -> tuple[bool, str]:
        async with self._lock:
            try:
                eid = self._slot_bytes_a_id(element)
            except (ValueError, json.JSONDecodeError) as exc:
                return False, f"Elemento inválido: {exc}"

            if eid is None:
                return False, "El elemento no tiene 'id' asignado."

            celda = self._gold_cells.setdefault(pos, Celda())
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
        self, pos: tuple[int, int], element_id: int
    ) -> tuple[bool, str]:
        async with self._lock:
            celda = self._gold_cells.get(pos)
            if celda is None:
                return False, f"No hay celda en {pos}."

            if celda.suelo == element_id:
                celda.suelo = None
            elif celda.bot == element_id:
                celda.bot = None
                self._bot_positions.pop(str(element_id), None)
            elif element_id in celda.resto:
                celda.resto.remove(element_id)
            else:
                return False, f"Elemento {element_id} no encontrado en {pos}."

            self._elements.pop(element_id, None)

            if celda.suelo is None and celda.bot is None and not celda.resto:
                self._gold_cells.pop(pos, None)

            return True, ""

    async def eliminar_avatar_bot(self, bot_id: str) -> tuple[bool, str]:
        pos = self._bot_positions.get(bot_id)
        if pos is None:
            return False, f"Bot {bot_id!r} no encontrado en bot_positions."

        async with self._lock:
            celda = self._gold_cells.get(pos)
            if celda is None or celda.bot is None:
                return False, f"No hay avatar de bot en {pos}."
            element_id = celda.bot

        return await self.eliminar_elemento(pos, element_id)

    async def matar_bot(
        self, bot_id: str, cause: str, tick_id: int
    ) -> tuple[bool, str]:
        ok, error = await self.eliminar_avatar_bot(bot_id)
        if not ok:
            logger.error(
                "matar_bot: no se pudo eliminar avatar de %s: %s", bot_id, error
            )
            return False, error

        if self._gestor_bots_client is None:
            logger.warning(
                "matar_bot: sin gestor_bots_client configurado — el script del bot %s no será terminado.",
                bot_id,
            )
            return True, ""

        try:
            await self._gestor_bots_client.matar_script_bot(bot_id)
        except Exception as exc:
            logger.error(
                "matar_bot: error pidiendo matar script de %s: %s", bot_id, exc
            )
            return False, str(exc)

        logger.info("Bot %s eliminado (causa=%s, tick=%d).", bot_id, cause, tick_id)
        return True, ""

    # ---- Acciones de bots ----

    async def resolver_accion(
        self, bot_id: str, action_type: str, payload: bytes
    ) -> ActionResult:
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

    # ---- Eventos globales ----

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

    # ---- Elementos globales (ciclo día/noche, lunar, clima...) ----

    async def avanzar_elementos_globales(self, tick_id: int) -> dict:
        cambios: dict = {}
        async with self._lock:
            for elem in self._elementos_globales.values():
                cambios.update(elem.tick(tick_id))
        return cambios

    async def get_elementos_globales(self) -> dict[str, dict]:
        """
        Devuelve un snapshot serializable (nombre → dict) de todos los
        elementos globales. Sustituye a GestorMundo.GetGlobalState
        (retirado, ver decisión "elementos_globales: B") — ahora vive
        aquí porque el estado de estos elementos siempre vivió en
        Logica_Mundo, no en Gestor_Mundo.
        """
        async with self._lock:
            return {
                nombre: elem.to_snapshot()
                for nombre, elem in self._elementos_globales.items()
            }

    async def obtener_celdas_en_region(
        self,
        min_pos: tuple[int, int],
        max_pos: tuple[int, int],
        excluir_min: Optional[tuple[int, int]] = None,
        excluir_max: Optional[tuple[int, int]] = None,
    ) -> list:
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
        async with self._lock:
            for cell in changed_cells:
                pos = (cell.pos.x, cell.pos.y)
                celda = self._cell_a_celda(cell)
                if celda.suelo is None and celda.bot is None and not celda.resto:
                    self._gold_cells.pop(pos, None)
                else:
                    self._gold_cells[pos] = celda

    async def consultar_representacion(
        self,
        min_pos: tuple[int, int],
        max_pos: tuple[int, int],
        incluir: list[str],
        modo: str,
    ) -> bytes:
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
                                n: str(v)
                                for n, v in comportamientos_encontrados.items()
                            },
                        }
                    )

        return json.dumps({"modo": modo, "elementos": resultado}).encode()

    async def save_snapshot(self, snapshot_id: str) -> None:
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
