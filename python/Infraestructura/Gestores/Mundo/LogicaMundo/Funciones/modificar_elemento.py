# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/modificar_elemento.py
"""
modificar_elemento — Implementación del RPC ModificarElemento.

La conversión patch (bytes JSON) → dict ocurre aquí, en la frontera de
red — logica_mundo.modificar_elemento() recibe ya un dict, coherente
con que su lógica no necesita saber nada del formato de transporte.
"""

import json
import logging

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb

logger = logging.getLogger(__name__)
NAME = "ModificarElemento"


async def handle(logica, request, context):
    pos = (request.pos.x, request.pos.y)
    try:
        patch = json.loads(request.patch.decode()) if request.patch else {}
    except json.JSONDecodeError as exc:
        logger.warning("ModificarElemento: patch inválido: %s", exc)
        return common_pb.Ack(ok=False, error=f"Patch inválido: {exc}")

    ok, error = await logica.modificar_elemento(pos, request.element_id, patch)
    return common_pb.Ack(ok=ok, error=error)
