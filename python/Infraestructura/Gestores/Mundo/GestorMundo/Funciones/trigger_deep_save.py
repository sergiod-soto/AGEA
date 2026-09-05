# Gestores/Mundo/Gestor_Mundo/funciones/trigger_deep_save.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import gestor_mundo_service_pb2 as pb
from Infraestructura.Gestores.Mundo.GestorMundo.gestor_mundo import GestorMundo
import logging

logger = logging.getLogger(__name__)
NAME = "TriggerDeepSave"

async def handle(gestor: GestorMundo, request, context) -> pb.TriggerDeepSaveResponse:
    try:
        await gestor._deep_save()
        return pb.TriggerDeepSaveResponse(ok=True, snapshot_id=gestor._snapshot_id)
    except Exception as e:
        logger.exception("Error en TriggerDeepSave")
        return pb.TriggerDeepSaveResponse(ok=False, error=str(e))