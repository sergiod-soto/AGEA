# Core/Entities/Mundo/Funciones/tipo_slot.py

from Core.Entities.Elementos.Simples.Bot.bot import Bot
from Core.Entities.Mundo.Suelo.suelo import Suelo


def tipo_slot_de(elemento) -> str:
    """
    Slot de celda que le corresponde a un elemento, decidido por su CLASE
    (no por un método del propio elemento):
      - hereda de Suelo -> "suelo" (Suelo_Piedra, Suelo_Tierra...)
      - es un Bot       -> "bot"
      - cualquier otra cosa -> "resto"
    Un único sitio decide esto, así Logica y Sector no pueden discrepar.
    """
    if isinstance(elemento, Suelo):
        return "suelo"
    if isinstance(elemento, Bot):
        return "bot"
    return "resto"