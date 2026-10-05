# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/generar_mundo.py
import logging

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb

logger = logging.getLogger(__name__)
NAME = "GenerarMundo"


async def handle(logica, request, context):
    """
    Inicia la generación del mundo y responde al instante: el trabajo real
    corre en segundo plano dentro de LogicaMundo. El cliente consulta el
    avance con EstadoGeneracionMundo (ver LogicaMundoClient.
    esperar_generacion_mundo). ok=False solo si ya había una en curso.
    Responde common.Ack, como el resto de RPC que solo informan de éxito/error.
    """
    try:
        ok, error = await logica.generar_mundo()
        return common_pb.Ack(ok=ok, error=error)
    except Exception as e:
        logger.exception("Error en GenerarMundo")
        return common_pb.Ack(ok=False, error=str(e))
