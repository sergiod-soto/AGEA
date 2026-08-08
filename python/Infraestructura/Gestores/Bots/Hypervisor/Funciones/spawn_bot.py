from Infraestructura.Gestores.Bots.Hypervisor.hypervisor import Hypervisor
import logging

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2

logger = logging.getLogger(__name__)
NAME = "SpawnBot"


async def handle(hv, request, context):
    cfg = request.config
    bot_config = {
        "bot_id": cfg.bot_id,
        "codigo_gz": bytes(cfg.codigo_gz),
        "budget": int(cfg.budget),
        "metadata": dict(cfg.metadata),
    }
    logger.info("SpawnBot: bot_id=%s", cfg.bot_id)
    try:
        result = await hv.spawn_bot(bot_config)
        return common_pb2.BotInfo(
            bot_id=cfg.bot_id,
            hypervisor_id=str(hv.hypervisor_id),
            ok=result.ok,
            error=result.error,
        )
    except Exception as e:
        logger.exception("Error en SpawnBot")
        return common_pb2.BotInfo(ok=False, error=str(e))
