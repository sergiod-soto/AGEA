# Infraestructura/Gestores/Mundo/Gestor_Mundo/ComandosConsola/advance_tick.py

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Mundo.GestorMundo.gestor_mundo import GestorMundo

TIPO = "AdvanceTick"


async def handle(gestor: GestorMundo, payload: bytes) -> bytes:
    """AdvanceTickRequest no tiene campos, así que ni hace falta parsear payload."""
    ok, error = gestor.avanza_tick()
    return common_pb2.Ack(ok=ok, error=error).SerializeToString()
