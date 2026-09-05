# Infraestructura/Gestores/Bots/Gestor_Bots/Funciones/matar_script_bot.py
"""
matar_script_bot.py — Implementación del RPC MatarScriptBot.

Origen: Logica_Mundo, tras decidir la muerte de un bot (combate,
inanición...) y eliminar su avatar del gold. Aquí solo se mata el
proceso/script en el Hypervisor correspondiente — Gestor_Bots no
necesita volver a tocar Logica_Mundo, porque el avatar ya se eliminó
antes de llegar aquí.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2

NAME = "MatarScriptBot"


async def handle(gestor, request, context):
    await gestor.kill_bot(request.bot_id)
    return common_pb2.Ack(ok=True)
