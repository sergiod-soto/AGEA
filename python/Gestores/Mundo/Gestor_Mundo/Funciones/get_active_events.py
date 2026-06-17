# Gestores/Mundo/Gestor_Mundo/funciones/get_active_events.py
from Gestores.Transporte.Proto_Generated.Sectores import gestor_mundo_service_pb2 as pb
from Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo

NAME = "GetActiveEvents"

async def handle(gestor: GestorMundo, request, context) -> pb.GetActiveEventsResponse:
    async with gestor._gold_lock:
        events = list(gestor._active_events.values())
    return pb.GetActiveEventsResponse(ok=True, events=events)