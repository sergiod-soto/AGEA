# freeze.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import common_pb2
import logging

logger = logging.getLogger(__name__)
NAME = "Freeze"


def handle(hv, request, context):
    """
    Pausa todos los bots del HV.
    En la implementación actual: marca un flag interno para que
    los bots no puedan gastar puntos hasta que se reanude.
    """
    try:
        hv.freeze()
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en Freeze")
        return common_pb2.Ack(ok=False, error=str(e))
