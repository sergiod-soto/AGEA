# resume.py
from Gestores.Transporte.Proto_Generated.Bots import common_pb2
import logging

logger = logging.getLogger(__name__)
NAME = "Resume"


def handle(hv, request, context):
    try:
        hv.resume()
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en Resume")
        return common_pb2.Ack(ok=False, error=str(e))
