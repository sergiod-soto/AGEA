# Gestores/Mundo/Sector/funciones/add_migrating_bot.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import sector_service_pb2 as pb
from Infraestructura.Gestores.Mundo.Sector.sector import Sector
import logging

logger = logging.getLogger(__name__)
NAME = "AddMigratingBot"

async def handle(sector: Sector, request, context) -> pb.AddMigratingBotResponse:
    try:
        sector.add_migrating_bot(tick_id=request.tick_id, bot=request.bot)
        return pb.AddMigratingBotResponse(ok=True)
    except Exception as e:
        logger.exception("Error en AddMigratingBot")
        return pb.AddMigratingBotResponse(ok=False, error=str(e))