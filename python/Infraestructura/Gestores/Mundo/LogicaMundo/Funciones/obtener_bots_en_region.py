# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/obtener_bots_en_region.py
import logging

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

logger = logging.getLogger(__name__)
NAME = "ObtenerBotsEnRegion"


async def handle(logica, request, context):
    """Bots (bot_id, id_elemento, pos) con avatar en la región pedida. Ver
    LogicaMundo.obtener_bots_en_region."""
    try:
        bots = await logica.obtener_bots_en_region(
            (request.min.x, request.min.y), (request.max.x, request.max.y)
        )
        return pb.ObtenerBotsEnRegionResponse(
            ok=True,
            bots=[
                common_pb.BotSnapshot(
                    bot_id=bot_id,
                    id_elemento=eid,
                    pos=common_pb.Position(x=pos[0], y=pos[1]),
                )
                for bot_id, eid, pos in bots
            ],
        )
    except Exception as e:
        logger.exception("Error en ObtenerBotsEnRegion")
        return pb.ObtenerBotsEnRegionResponse(ok=False, error=str(e))
