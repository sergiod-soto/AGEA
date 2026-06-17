# Gestores/Mundo/Gestor_Mundo/funciones/spawn_global_event.py
from Gestores.Transporte.Proto_Generated.Sectores import gestor_mundo_service_pb2 as pb
from Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo
import logging

logger = logging.getLogger(__name__)
NAME = "SpawnGlobalEvent"

async def handle(gestor: GestorMundo, request, context) -> pb.SpawnGlobalEventResponse:
    event = request.event
    try:
        async with gestor._gold_lock:
            gestor._active_events[event.event_id] = event
            if event.HasField("pos"):
                key = (event.pos.x, event.pos.y)
                gestor._gold_cells[key] = event.payload
                await gestor._distribuir_celda_modificada(key, event.payload)
        logger.info("Evento global spawneado: %s (%s)", event.event_id, event.type)
        return pb.SpawnGlobalEventResponse(ok=True, event_id=event.event_id)
    except Exception as e:
        logger.exception("Error en SpawnGlobalEvent")
        return pb.SpawnGlobalEventResponse(ok=False, error=str(e))