# Infraestructura/Gestores/Mundo/Gestor_Mundo/Funciones/heartbeat.py
"""
heartbeat.py — Implementación del RPC Heartbeat.

Rellena sector_statuses con los sectores detectados caídos por
fallos consecutivos de StartTick/GetDelta (ver
GestorMundo.sectores_caidos()). ok=False si hay al menos uno — misma
convención que Gestor_Bots.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2 as pb,
)
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2

NAME = "Heartbeat"


async def handle(gestor, request, context):
    caidos = gestor.sectores_caidos()
    sector_statuses = [
        common_pb2.SectorStatus(sector_id=sid, alive=False) for sid in caidos
    ]
    if caidos:
        return pb.GestorMundoHeartbeatResponse(
            ok=False,
            error=f"Sectores sin respuesta: {caidos}",
            sector_statuses=sector_statuses,
        )
    return pb.GestorMundoHeartbeatResponse(ok=True, error="")
