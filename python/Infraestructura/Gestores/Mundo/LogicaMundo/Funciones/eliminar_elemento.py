# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/eliminar_elemento.py
"""
eliminar_elemento.py — Implementación del RPC EliminarElemento.

Identifica el elemento a eliminar por su id (no por type_id): el
propio id ya determina en qué slot de la celda está, sin necesidad de
que quien llama sepa de antemano si es "suelo", "bot" o parte de "resto".
"""

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb

NAME = "EliminarElemento"


async def handle(logica, request, context):
    pos = (request.pos.x, request.pos.y)
    ok, error = await logica.eliminar_elemento(pos, request.element_id)
    return common_pb.Ack(ok=ok, error=error)
