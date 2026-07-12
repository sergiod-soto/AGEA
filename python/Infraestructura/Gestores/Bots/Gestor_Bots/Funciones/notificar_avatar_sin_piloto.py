# Infraestructura/Gestores/Bots/Gestor_Bots/Funciones/notificar_avatar_sin_piloto.py
"""
notificar_avatar_sin_piloto.py — Implementación del RPC NotificarAvatarSinPiloto.

Origen: el propio Hypervisor, cuando detecta que el script de un bot se
ha roto (no compila, excepción no controlada, o cualquier fallo que
detenga su ejecución). El HV ya gestiona su proceso localmente — lo
único que falta es que Logica_Mundo elimine el avatar, que se ha
quedado "sin piloto". Gestor_Bots actúa de puente, sin lógica propia.
"""

import logging

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2

logger = logging.getLogger(__name__)

NAME = "NotificarAvatarSinPiloto"


async def handle(gestor, request, context):
    ok, error = await gestor.eliminar_avatar_bot(request.bot_id)
    if not ok:
        logger.warning(
            "NotificarAvatarSinPiloto: no se pudo eliminar avatar de %s: %s",
            request.bot_id, error,
        )
    return common_pb2.Ack(ok=ok, error=error)