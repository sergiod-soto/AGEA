# Gestores/Bots/Gestor_Bots/Funciones/notify_bot_death.py
from Gestores.Transporte.Proto_Generated.Bots import common_pb2
import logging
logger = logging.getLogger(__name__)
NAME = "NotifyBotDeath"

async def handle(gestor, request, context):
    """
    El HV notifica que un bot murió (script colgado o error).
    El gestor elimina el bot de su registro y notifica al Mundo.
    """
    logger.info("NotifyBotDeath: bot=%s causa=%s tick=%d",
                request.bot_id, request.cause, request.tick)
    try:
        await gestor.notify_bot_death_async(
            bot_id=request.bot_id,
            cause=request.cause,
            tick=request.tick,
        )
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en NotifyBotDeath")
        return common_pb2.Ack(ok=False, error=str(e))