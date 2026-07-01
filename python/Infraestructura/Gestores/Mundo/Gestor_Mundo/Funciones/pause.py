# Gestores/Mundo/Gestor_Mundo/funciones/pause.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import gestor_mundo_service_pb2 as pb
from Infraestructura.Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo
import logging

logger = logging.getLogger(__name__)
NAME = "Pause"

async def handle(gestor: GestorMundo, request, context) -> pb.PauseResponse:
    try:
        await gestor.freeze()
        return pb.PauseResponse(ok=True)
    except Exception as e:
        logger.exception("Error en Pause")
        return pb.PauseResponse(ok=False, error=str(e))