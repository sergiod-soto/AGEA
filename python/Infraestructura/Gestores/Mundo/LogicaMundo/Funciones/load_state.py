# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/load_state.py
import logging

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb

logger = logging.getLogger(__name__)
NAME = "LoadState"


async def handle(logica, request, context):
    """
    Restaura el estado de LogicaMundo desde un snapshot. LogicaMundo.load_state
    devuelve (ok, error): antes respondía ok=True aunque el snapshot no
    existiera, y el cliente lo daba por bueno. Ahora el fallo llega tal cual y
    LogicaMundoClient.load_state lo convierte en RuntimeError (fatal al
    arrancar). El RPC devuelve common.Ack (así está en el .proto).
    """
    try:
        ok, error = await logica.load_state(request.snapshot_id)
        return common_pb.Ack(ok=ok, error=error)
    except Exception as e:
        logger.exception("Error en LoadState")
        return common_pb.Ack(ok=False, error=str(e))
