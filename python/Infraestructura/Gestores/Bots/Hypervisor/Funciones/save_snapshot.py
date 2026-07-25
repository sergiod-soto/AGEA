# save_snapshot.py
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
import logging

logger = logging.getLogger(__name__)
NAME = "SaveSnapshot"


async def handle(hv, request, context):
    try:
        await hv.save_snapshot(request.snapshot_id)
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en SaveSnapshot")
        return common_pb2.Ack(ok=False, error=str(e))
