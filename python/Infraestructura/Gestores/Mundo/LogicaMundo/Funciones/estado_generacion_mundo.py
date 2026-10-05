# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/estado_generacion_mundo.py
import logging

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

logger = logging.getLogger(__name__)
NAME = "EstadoGeneracionMundo"


async def handle(logica, request, context):
    """
    Devuelve (estado, progreso 0.0-1.0, error de generación). No toma el lock
    de LogicaMundo (estado_generacion() es síncrono y sin lock a propósito):
    el generador lo mantiene durante toda la generación, y si el sondeo lo
    pidiera no recibiría respuesta hasta el final.

    Hay DOS campos de error distintos: `error` es un fallo del propio RPC
    (ok=False); `error_generacion` es el motivo por el que la generación
    terminó en ERROR (con ok=True: el RPC funcionó, lo que falló fue otra cosa).
    """
    try:
        estado, progreso, error_generacion = logica.estado_generacion()
        # int(estado): EstadoGeneracion (IntEnum) tiene los mismos valores que
        # el enum del .proto.
        return pb.EstadoGeneracionMundoResponse(
            ok=True,
            estado=int(estado),
            progreso=progreso,
            error_generacion=error_generacion,
        )
    except Exception as e:
        logger.exception("Error en EstadoGeneracionMundo")
        return pb.EstadoGeneracionMundoResponse(ok=False, error=str(e))
