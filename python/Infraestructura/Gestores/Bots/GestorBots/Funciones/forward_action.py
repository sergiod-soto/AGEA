# Infraestructura/Gestores/Bots/Gestor_Bots/Funciones/forward_action.py
"""
forward_action.py — Implementación del RPC ForwardAction.

Pide a Logica_Mundo que resuelva una acción de bot recibida desde el
Hypervisor. Antes llamaba a gestor.forward_action_to_mundo(); ese método
se renombró a resolver_accion_bot() al migrar la resolución de acciones
de GestorMundo a Logica_Mundo (ver gestor_bots.py).
"""

import logging

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2

logger = logging.getLogger(__name__)

NAME = "ForwardAction"


async def handle(gestor, request, context):
    logger.debug("ForwardAction: bot=%s tipo=%s", request.bot_id, request.action_type)
    try:
        result = await gestor.resolver_accion_bot(
            bot_id=request.bot_id,
            hypervisor_id=request.hypervisor_id,
            action_type=request.action_type,
            payload=request.payload,
        )
        return common_pb2.ActionResult(
            ok=result.ok, payload=result.payload, error=result.error
        )
    except Exception as e:
        logger.exception("Error en ForwardAction")
        return common_pb2.ActionResult(ok=False, error=str(e))
