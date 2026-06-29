# Gestores/Bots/Gestor_Bots/funciones/forward_action.py
from Gestores.Transporte.Proto_Generated.Bots import common_pb2
from Gestores.Bots.Gestor_Bots.gestor_bots import Gestor_Bots
import logging

logger = logging.getLogger(__name__)
NAME = "ForwardAction"


async def handle(gestor, request, context):
    from Gestores.Transporte.Proto_Generated.Bots import common_pb2
    import logging

    logger = logging.getLogger(__name__)
    logger.debug("ForwardAction: bot=%s tipo=%s", request.bot_id, request.action_type)
    try:
        result = await gestor.forward_action_to_mundo(
            bot_id=request.bot_id,
            hypervisor_id=request.hypervisor_id,
            action_type=request.action_type,
            payload=request.payload,
        )
        return common_pb2.ActionResult(
            ok=result.ok, payload=result.payload, error=result.error
        )
    except Exception as e:
        logger.exception("Error en ForwardAction")
        return common_pb2.ActionResult(ok=False, error=str(e))
