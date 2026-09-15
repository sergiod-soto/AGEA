# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/crear_elemento.py
"""
crear_elemento.py — Implementación del RPC CrearElemento.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb

NAME = "CrearElemento"


async def handle(logica, request, context):
    pos = (request.pos.x, request.pos.y)
    ok, error = await logica.crear_elemento(pos, request.type_id, request.element)
    return common_pb.Ack(ok=ok, error=error)
