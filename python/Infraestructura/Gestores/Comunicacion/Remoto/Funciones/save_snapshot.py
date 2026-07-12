# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/save_snapshot.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    gestor_bots_service_pb2 as pb,
)

COMPONENTE = "GESTOR_BOTS"
OPERACION = "SaveSnapshot"


async def handle(clientes, payload: bytes) -> bytes:
    req = pb.SaveSnapshotRequest()
    req.ParseFromString(payload)

    ok, error = await clientes.gestor_bots.save_snapshot(req.snapshot_id)
    resp = pb.SaveSnapshotResponse(ok=ok, error=error, snapshot_id=req.snapshot_id)
    return resp.SerializeToString()
