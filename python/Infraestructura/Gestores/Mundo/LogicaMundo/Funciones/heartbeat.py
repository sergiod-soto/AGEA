# Infraestructura/Gestores/Mundo/Logica_Mundo/Funciones/heartbeat.py
"""
heartbeat.py — Implementación mínima del RPC Heartbeat.

Solo confirma que el proceso responde. MonitorComponentes (remote.py)
únicamente comprueba que la llamada no lance excepción — no inspecciona
el contenido de la respuesta.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

NAME = "Heartbeat"


async def handle(logica, request, context):
    return pb.LogicaMundoHeartbeatResponse(ok=True, error="")
