# Gestores/Bots/Hypervisor/Funciones/freeze.py
"""
Migrado a asyncio junto con Hypervisor: hv.freeze() ahora es async.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
import logging

logger = logging.getLogger(__name__)
NAME = "Freeze"


async def handle(hv, request, context):
    """
    Pausa todos los bots del HV.
    En la implementación actual: marca un flag interno para que
    los bots no puedan gastar puntos hasta que se reanude.
    """
    try:
        await hv.freeze()
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en Freeze")
        return common_pb2.Ack(ok=False, error=str(e))
