# Gestores/Mundo/Gestor_Mundo/funciones/get_snapshot_info.py
import json
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import gestor_mundo_service_pb2 as pb
from Infraestructura.Gestores.Mundo.GestorMundo.gestor_mundo import GestorMundo
import logging

logger = logging.getLogger(__name__)
NAME = "GetSnapshotInfo"

async def handle(gestor: GestorMundo, request, context) -> pb.GetSnapshotInfoResponse:
    path = gestor._latest_snapshot_path()
    if path is None:
        return pb.GetSnapshotInfoResponse(ok=False, error="No hay snapshots disponibles.")
    try:
        data = json.loads(path.read_text())
        return pb.GetSnapshotInfoResponse(
            ok=True,
            snapshot_id=data.get("snapshot_id", ""),
            tick_id=data.get("tick_id", 0),
            timestamp_unix=int(path.stat().st_mtime),
            is_deep_snapshot="deep" in data.get("snapshot_id", ""),
        )
    except Exception as e:
        logger.exception("Error leyendo snapshot info")
        return pb.GetSnapshotInfoResponse(ok=False, error=str(e))