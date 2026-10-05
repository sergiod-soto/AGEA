# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/matar_bot.py
import logging

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb

logger = logging.getLogger(__name__)
NAME = "MatarBot"


async def handle(logica, request, context):
    """
    Lo llama Gestor_Mundo cuando un Sector informa de una muerte
    (dead_bot_ids) o cuando un movimiento externo se pierde. LogicaMundo
    elimina el avatar (si sigue ahí) y pide terminar el script del bot.
    Responde common.Ack, igual que EliminarAvatarBot.
    """
    try:
        ok, error = await logica.matar_bot(
            request.bot_id, request.cause, request.tick_id
        )
        return common_pb.Ack(ok=ok, error=error)
    except Exception as e:
        logger.exception("Error en MatarBot")
        return common_pb.Ack(ok=False, error=str(e))
