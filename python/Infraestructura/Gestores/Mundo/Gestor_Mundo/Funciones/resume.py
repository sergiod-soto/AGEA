# Gestores/Mundo/Gestor_Mundo/funciones/resume.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import gestor_mundo_service_pb2 as pb
from Infraestructura.Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo
import logging

logger = logging.getLogger(__name__)
NAME = "Resume"

async def handle(gestor: GestorMundo, request, context) -> pb.ResumeResponse:
    try:
        await gestor.resume()
        return pb.ResumeResponse(ok=True)
    except Exception as e:
        logger.exception("Error en Resume")
        return pb.ResumeResponse(ok=False, error=str(e))