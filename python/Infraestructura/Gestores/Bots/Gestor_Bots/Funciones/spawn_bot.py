# Gestores/Bots/Gestor_Bots/Funciones/spawn_bot.py
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Bots.Gestor_Bots.gestor_bots import Gestor_Bots
import logging

logger = logging.getLogger(__name__)
NAME = "SpawnBot"


async def handle(gestor: Gestor_Bots, request, context):
    cfg = request.config
    bot_config = {
        "bot_id": cfg.bot_id,
        "codigo_gz": cfg.codigo_gz,
        "budget": cfg.budget,
        "metadata": dict(cfg.metadata),
    }
    logger.info("SpawnBot: bot_id=%s", cfg.bot_id)
    try:
        info = await gestor.spawn_bot(bot_config)
    except Exception as e:
        logger.exception("Error en SpawnBot")
        return common_pb2.BotInfo(ok=False, error=str(e))

    return common_pb2.BotInfo(
        bot_id=info.bot_id,
        hypervisor_id=info.hypervisor_id,
        proxy_address=info.proxy_address,
        ok=info.ok,
        error=info.error,
    )
