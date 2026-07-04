# Infraestructura/Gestores/Mundo/Gestor_Mundo/Funciones/despawn_global_event.py
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo
import logging

logger = logging.getLogger(__name__)

NAME = "DespawnGlobalEvent"


async def handle(gestor: GestorMundo, request, context) -> common_pb2.Ack:
    try:
        async with gestor._gold_lock:
            event = gestor._active_events.pop(request.event_id, None)
            if event is None:
                return common_pb2.Ack(
                    ok=False, error=f"Evento '{request.event_id}' no encontrado."
                )
            # Solo hay celda gold que limpiar si el evento tenía posición
            # (algunos eventos globales, como ciclos día/noche, no la tienen).
            if event.HasField("pos"):
                key = (event.pos.x, event.pos.y)
                gestor._gold_cells.pop(key, None)
                await gestor._distribute_gold_to_sectors()
        logger.info("Evento global despawneado: %s (razón: %s)", request.event_id, request.reason)
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en DespawnGlobalEvent")
        return common_pb2.Ack(ok=False, error=str(e))