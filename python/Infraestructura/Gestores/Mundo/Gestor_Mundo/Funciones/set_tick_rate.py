from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import common_pb2
import logging

logger = logging.getLogger(__name__)
NAME = "SetTickRate"


async def handle(gestor, request, context):
    try:
        gestor.set_tick_rate(request.ticks_per_second)
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en SetTickRate")
        return common_pb2.Ack(ok=False, error=str(e))
