# Gestores/Bots/Hypervisor/funciones/spawn_bot.py
from Gestores.Transporte.Proto_Generated.Bots import common_pb2
from Gestores.Bots.Hypervisor.hypervisor import Hypervisor
import logging

logger = logging.getLogger(__name__)
NAME = "SpawnBot"

def handle(hv: Hypervisor, request, context):
    cfg = request.config
    bot_config = {
        "bot_id": cfg.bot_id,
        "codigo_gz": cfg.codigo_gz,
        "budget": cfg.budget,
        "metadata": dict(cfg.metadata),
    }
    logger.info("SpawnBot: bot_id=%s", cfg.bot_id)
    try:
        info = hv.spawn_bot(bot_config)
        return common_pb2.BotInfo(
            bot_id=info.bot_id, hypervisor_id=info.hypervisor_id,
            ok=info.ok, error=info.error,
        )
    except Exception as e:
        logger.exception("Error en SpawnBot")
        return common_pb2.BotInfo(ok=False, error=str(e))