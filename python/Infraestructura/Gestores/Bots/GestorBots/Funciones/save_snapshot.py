# Gestores/Bots/Gestor_Bots/Funciones/save_snapshot.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import gestor_bots_service_pb2 as pb
import logging

logger = logging.getLogger(__name__)
NAME = "SaveSnapshot"


async def handle(gestor, request, context):
    try:
        await gestor.save_snapshot_async(request.snapshot_id)
        return pb.SaveSnapshotResponse(ok=True, snapshot_id=request.snapshot_id)
    except Exception as e:
        logger.exception("Error en SaveSnapshot")
        return pb.SaveSnapshotResponse(ok=False, error=str(e))
