# Gestores/Mundo/Gestor_Mundo/funciones/despawn_global_event.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import gestor_mundo_service_pb2 as pb
from Infraestructura.Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo
import logging

logger = logging.getLogger(__name__)
NAME = "DespawnGlobalEvent"

async def handle(gestor: GestorMundo, request, context) -> pb.DespawnGlobalEventResponse:
    try:
        async with gestor._gold_lock:
            event = gestor._active_events.pop(request.event_id, None)
            if event is None:
                return pb.DespawnGlobalEventResponse(
                    ok=False, error=f"Evento '{request.event_id}' no encontrado."
                )
            if event.HasField("pos"):
                key = (event.pos.x, event.pos.y)
                gestor._gold_cells.pop(key, None)
                await gestor._distribuir_celda_modificada(key, b"")
        logger.info("Evento global despawneado: %s (razón: %s)", request.event_id, request.reason)
        return pb.DespawnGlobalEventResponse(ok=True)
    except Exception as e:
        logger.exception("Error en DespawnGlobalEvent")
        return pb.DespawnGlobalEventResponse(ok=False, error=str(e))