# Infraestructura/Gestores/Mundo/Logica_Mundo/Funciones/eliminar_avatar_bot.py
"""
eliminar_avatar_bot.py — Implementación del RPC EliminarAvatarBot.

Flujo B: el Hypervisor detectó que el script de un bot se rompió y, vía
Gestor_Bots, pide aquí eliminar su avatar del gold. No requiere conocer
posición ni element_id — logica_mundo.eliminar_avatar_bot() los resuelve
internamente a partir de bot_id.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2

NAME = "EliminarAvatarBot"


async def handle(logica, request, context):
    ok, error = await logica.eliminar_avatar_bot(request.bot_id)
    return common_pb2.Ack(ok=ok, error=error)
