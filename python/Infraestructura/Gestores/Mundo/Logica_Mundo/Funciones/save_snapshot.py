# Infraestructura/Gestores/Mundo/Logica_Mundo/Funciones/save_snapshot.py
"""
save_snapshot.py — Implementación del RPC SaveSnapshot.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

NAME = "SaveSnapshot"


async def handle(logica, request, context):
    await logica.save_snapshot(request.snapshot_id)
    return pb.SaveSnapshotResponse(ok=True, error="", snapshot_id=request.snapshot_id)