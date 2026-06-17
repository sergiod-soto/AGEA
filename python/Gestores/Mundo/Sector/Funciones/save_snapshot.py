# Gestores/Mundo/Sector/funciones/save_snapshot.py
from Gestores.Transporte.Proto_Generated.Sectores import sector_service_pb2 as pb
from Gestores.Mundo.Sector.sector import Sector
import logging

logger = logging.getLogger(__name__)
NAME = "SaveSnapshot"

async def handle(sector: Sector, request, context) -> pb.SaveSnapshotResponse:
    try:
        await sector.save_snapshot(snapshot_id=request.snapshot_id)
        return pb.SaveSnapshotResponse(ok=True, snapshot_id=request.snapshot_id)
    except Exception as e:
        logger.exception("Error en SaveSnapshot")
        return pb.SaveSnapshotResponse(ok=False, error=str(e))
    