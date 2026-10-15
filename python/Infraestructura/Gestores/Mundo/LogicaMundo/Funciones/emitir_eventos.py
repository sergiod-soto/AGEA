# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/emitir_eventos.py


import logging

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb

logger = logging.getLogger(__name__)
NAME = "EmitirEventos"


async def handle(logica, request, context):
    """Emite en el bus de Logica los eventos que el Gestor recogió de los Sectores."""
    try:
        await logica.emitir_eventos(list(request.eventos))
        return common_pb.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en EmitirEventos")
        return common_pb.Ack(ok=False, error=str(e))
