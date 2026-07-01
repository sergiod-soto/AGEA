# Gestores/Mundo/Gestor_Mundo/funciones/forward_action.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import gestor_mundo_service_pb2 as pb
from Infraestructura.Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo
import logging

logger = logging.getLogger(__name__)
NAME = "ForwardAction"

async def handle(gestor: GestorMundo, request, context) -> pb.ForwardActionResponse:
    try:
        result = await gestor.handle_action(
            bot_id=request.bot_id,
            action_type=request.action_type,
            payload=request.payload,
        )
        return pb.ForwardActionResponse(
            ok=result.ok,
            error=result.error,
            payload=result.payload,
            tick_id=gestor._tick_id,
        )
    except Exception as e:
        logger.exception("Error en ForwardAction")
        return pb.ForwardActionResponse(ok=False, error=str(e))