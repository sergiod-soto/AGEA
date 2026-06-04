"""
gestor_mundo_servicer.py
------------------------
Implementación gRPC del GestorMundoService.
Recibe llamadas del nodo principal y las delega a GestorMundo.

Carpeta: Gestores/Mundo/Gestor_Mundo/
"""

import json
import logging
import time

import grpc

from Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2 as pb,
    gestor_mundo_service_pb2_grpc as pb_grpc,
)
from Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo, SystemState

logger = logging.getLogger(__name__)

# Tamaño de batch para streaming de GetWorldMap.
# El servidor decide cuántas celdas por mensaje — ajustable en caliente.
WORLDMAP_BATCH_SIZE = 1000


class GestorMundoServicer(pb_grpc.GestorMundoServiceServicer):

    def __init__(self, gestor: GestorMundo) -> None:
        self._g = gestor

    # ─────────────────────────────────────────────
    #  Helpers
    # ─────────────────────────────────────────────

    def _require_paused(self, context: grpc.ServicerContext) -> bool:
        """Aborta la llamada si el sistema no está pausado. Devuelve True si ok."""
        if self._g._state != SystemState.PAUSED:
            context.abort(
                grpc.StatusCode.FAILED_PRECONDITION,
                "Operación solo permitida con el mundo en pausa.",
            )
            return False
        return True

    # ─────────────────────────────────────────────
    #  Consulta del mundo
    # ─────────────────────────────────────────────

    async def GetWorldMap(self, request, context):
        """
        Streaming server-side. Emite batches de celdas del estado gold.
        Si only_active_sectors=True, filtra solo celdas de sectores ACTIVOS/DORMIDOS.
        """
        from Gestores.Mundo.Gestor_Mundo.gestor_mundo import SectorMode
        from Gestores.Transporte.Proto_Generated.Mundo.sector_service_pb2 import (
            Position,
        )

        async with self._g._gold_lock:
            gold_snapshot = dict(self._g._gold_cells)
            sectores = dict(self._g._sectores)

        # Precomputar celdas válidas de sectores activos si hace falta
        if request.only_active_sectors:
            from Gestores.Mundo.Gestor_Mundo.gestor_mundo import SECTOR_SIZE

            celdas_validas = set()
            for (col, row), info in sectores.items():
                if info.mode in (SectorMode.ACTIVO, SectorMode.DORMIDO):
                    x0 = col * SECTOR_SIZE
                    y0 = row * SECTOR_SIZE
                    x1 = x0 + SECTOR_SIZE
                    y1 = y0 + SECTOR_SIZE
                    for x, y in gold_snapshot:
                        if x0 <= x < x1 and y0 <= y < y1:
                            celdas_validas.add((x, y))
        else:
            celdas_validas = set(gold_snapshot.keys())

        batch = []
        for x, y in celdas_validas:
            element = gold_snapshot[(x, y)]
            cell = pb.Cell(
                pos=pb.Position(x=x, y=y),
                # type_id viene embebido en el elemento serializado;
                # el receptor usa el registry para deserializar.
                # TODO: exponer type_id explícitamente si el cliente lo necesita.
                element=element,
            )
            batch.append(cell)
            if len(batch) >= WORLDMAP_BATCH_SIZE:
                yield pb.GetWorldMapResponse(cells=batch)
                batch = []

        if batch:
            yield pb.GetWorldMapResponse(cells=batch)

    async def GetGlobalState(self, request, context):
        elementos = []
        for elem in self._g._elementos_globales:
            elementos.append(
                pb.GlobalElementState(
                    name=elem.__class__.__name__,
                    state=json.dumps(elem.to_snapshot()).encode(),
                )
            )
        return pb.GetGlobalStateResponse(
            ok=True,
            tick_id=self._g._tick_id,
            snapshot_id=self._g._snapshot_id,
            elementos_globales=elementos,
        )

    async def GetSnapshotInfo(self, request, context):
        path = self._g._latest_snapshot_path()
        if path is None:
            return pb.GetSnapshotInfoResponse(
                ok=False,
                error="No hay snapshots disponibles.",
            )
        try:
            data = json.loads(path.read_text())
            return pb.GetSnapshotInfoResponse(
                ok=True,
                snapshot_id=data.get("snapshot_id", ""),
                tick_id=data.get("tick_id", 0),
                timestamp_unix=int(path.stat().st_mtime),
                is_deep_snapshot="deep" in data.get("snapshot_id", ""),
            )
        except Exception as e:
            logger.exception("Error leyendo snapshot info")
            return pb.GetSnapshotInfoResponse(ok=False, error=str(e))

    # ─────────────────────────────────────────────
    #  Control del ciclo de vida
    # ─────────────────────────────────────────────

    async def Pause(self, request, context):
        try:
            await self._g.freeze()
            return pb.PauseResponse(ok=True)
        except Exception as e:
            logger.exception("Error en Pause")
            return pb.PauseResponse(ok=False, error=str(e))

    async def Resume(self, request, context):
        try:
            await self._g.resume()
            return pb.ResumeResponse(ok=True)
        except Exception as e:
            logger.exception("Error en Resume")
            return pb.ResumeResponse(ok=False, error=str(e))

    async def SetTickSpeed(self, request, context):
        factor = request.speed_factor
        if factor < 0:
            return pb.SetTickSpeedResponse(
                ok=False,
                error="speed_factor no puede ser negativo.",
                effective_factor=self._g._speed_factor,
            )

        # 0.0 equivale a pausa
        if factor == 0.0:
            await self._g.freeze()
            self._g._speed_factor = 0.0
            return pb.SetTickSpeedResponse(ok=True, effective_factor=0.0)

        # Límite superior configurable (evitar ticks infinitamente rápidos)
        MAX_FACTOR = 10.0
        effective = min(factor, MAX_FACTOR)
        self._g._speed_factor = effective

        # Si estaba pausado por speed=0, reanudar
        if self._g._state == SystemState.PAUSED:
            await self._g.resume()

        return pb.SetTickSpeedResponse(ok=True, effective_factor=effective)

    async def TriggerDeepSave(self, request, context):
        try:
            await self._g._deep_save()
            return pb.TriggerDeepSaveResponse(
                ok=True,
                snapshot_id=self._g._snapshot_id,
            )
        except Exception as e:
            logger.exception("Error en TriggerDeepSave")
            return pb.TriggerDeepSaveResponse(ok=False, error=str(e))

    # ─────────────────────────────────────────────
    #  Eventos globales
    # ─────────────────────────────────────────────

    async def SpawnGlobalEvent(self, request, context):
        event = request.event
        try:
            async with self._g._gold_lock:
                self._g._active_events[event.event_id] = event

                # Si el evento tiene posición, insertar en el gold
                if event.HasField("pos"):
                    key = (event.pos.x, event.pos.y)
                    # El payload del evento actúa como elemento en esa celda
                    self._g._gold_cells[key] = event.payload
                    # Distribuir la celda afectada a los sectores correspondientes
                    await self._g._distribuir_celda_modificada(key, event.payload)

            logger.info("Evento global spawneado: %s (%s)", event.event_id, event.type)
            return pb.SpawnGlobalEventResponse(ok=True, event_id=event.event_id)
        except Exception as e:
            logger.exception("Error en SpawnGlobalEvent")
            return pb.SpawnGlobalEventResponse(ok=False, error=str(e))

    async def DespawnGlobalEvent(self, request, context):
        try:
            async with self._g._gold_lock:
                event = self._g._active_events.pop(request.event_id, None)
                if event is None:
                    return pb.DespawnGlobalEventResponse(
                        ok=False,
                        error=f"Evento '{request.event_id}' no encontrado.",
                    )

                # Si tenía posición, eliminar del gold
                if event.HasField("pos"):
                    key = (event.pos.x, event.pos.y)
                    self._g._gold_cells.pop(key, None)
                    await self._g._distribuir_celda_modificada(key, b"")

            logger.info(
                "Evento global despawneado: %s (razón: %s)",
                request.event_id,
                request.reason,
            )
            return pb.DespawnGlobalEventResponse(ok=True)
        except Exception as e:
            logger.exception("Error en DespawnGlobalEvent")
            return pb.DespawnGlobalEventResponse(ok=False, error=str(e))

    async def GetActiveEvents(self, request, context):
        async with self._g._gold_lock:
            events = list(self._g._active_events.values())
        return pb.GetActiveEventsResponse(ok=True, events=events)

    # ─────────────────────────────────────────────
    #  Modificación en caliente (solo dev, requiere pausa)
    # ─────────────────────────────────────────────

    async def ModifyElement(self, request, context):
        if not self._require_paused(context):
            return pb.ModifyElementResponse(ok=False)
        try:
            key = (request.pos.x, request.pos.y)
            async with self._g._gold_lock:
                if key not in self._g._gold_cells:
                    return pb.ModifyElementResponse(
                        ok=False,
                        error=f"No hay elemento en ({key[0]},{key[1]}).",
                    )
                # Aplicar patch: sobrescribir el elemento serializado completo.
                # La validación de type_id la hace el cliente o una capa superior.
                # TODO: merge parcial de campos proto cuando el registry esté disponible.
                self._g._gold_cells[key] = request.patch
                await self._g._distribuir_celda_modificada(key, request.patch)

            logger.info(
                "[DEV] ModifyElement en (%d,%d) type=%s",
                request.pos.x,
                request.pos.y,
                request.type_id,
            )
            return pb.ModifyElementResponse(ok=True)
        except Exception as e:
            logger.exception("Error en ModifyElement")
            return pb.ModifyElementResponse(ok=False, error=str(e))

    async def CreateElement(self, request, context):
        if not self._require_paused(context):
            return pb.CreateElementResponse(ok=False)
        try:
            key = (request.pos.x, request.pos.y)
            async with self._g._gold_lock:
                if key in self._g._gold_cells:
                    return pb.CreateElementResponse(
                        ok=False,
                        error=f"Ya existe un elemento en ({key[0]},{key[1]}).",
                    )
                self._g._gold_cells[key] = request.element
                await self._g._distribuir_celda_modificada(key, request.element)

            logger.info(
                "[DEV] CreateElement en (%d,%d) type=%s",
                request.pos.x,
                request.pos.y,
                request.type_id,
            )
            return pb.CreateElementResponse(ok=True)
        except Exception as e:
            logger.exception("Error en CreateElement")
            return pb.CreateElementResponse(ok=False, error=str(e))

    async def DeleteElement(self, request, context):
        if not self._require_paused(context):
            return pb.DeleteElementResponse(ok=False)
        try:
            key = (request.pos.x, request.pos.y)
            async with self._g._gold_lock:
                if key not in self._g._gold_cells:
                    return pb.DeleteElementResponse(
                        ok=False,
                        error=f"No hay elemento en ({key[0]},{key[1]}).",
                    )
                self._g._gold_cells.pop(key)
                await self._g._distribuir_celda_modificada(key, b"")

            logger.info("[DEV] DeleteElement en (%d,%d)", request.pos.x, request.pos.y)
            return pb.DeleteElementResponse(ok=True)
        except Exception as e:
            logger.exception("Error en DeleteElement")
            return pb.DeleteElementResponse(ok=False, error=str(e))
