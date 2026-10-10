# Core/Entities/Mundo/Celda/celda.py
"""
Celda: contenedor de los elementos que ocupan una posición del mundo.

Tres slots, igual que usaba Logica_Mundo:
- suelo: como mucho un elemento (id) de tipo suelo.
- bot:   como mucho un elemento (id) de tipo bot.
- resto: cualquier cantidad de elementos (ids) de cualquier otro tipo.

Todo se guarda por id (int), nunca por objeto: el objeto real vive en
Mundo.elementos. Es intencional -- una única fuente de verdad para el
estado del elemento, y hace trivial serializar la celda (solo ids).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional



@dataclass
class Celda:
    suelo: int = None
    bot: Optional[int] = None
    resto: list[int] = field(default_factory=list)

    def put_elemento(self, eid: int, tipo_slot: str) -> None:
        """
        Coloca 'eid' en el slot indicado ('suelo', 'bot', o cualquier otro
        valor -> 'resto'). Sobrescribe sin comprobar ocupación previa.
        """
        if tipo_slot == "suelo":
            self.suelo = eid
        elif tipo_slot == "bot":
            self.bot = eid
        else:
            self.resto.append(eid)

    def tipo_slot_de(self, eid: int) -> Optional[str]:
        """En qué slot está 'eid' ('suelo'/'bot'/'resto'), o None si no
        está en esta celda."""
        if self.suelo == eid:
            return "suelo"
        if self.bot == eid:
            return "bot"
        if eid in self.resto:
            return "resto"
        return None

    def remove_elemento(self, eid: int) -> bool:
        """Quita 'eid' de la celda, sea cual sea su slot. False si no
        estaba en ninguno."""
        tipo = self.tipo_slot_de(eid)
        if tipo == "suelo":
            self.suelo = None
        elif tipo == "bot":
            self.bot = None
        elif tipo == "resto":
            self.resto.remove(eid)
        else:
            return False
        return True

    def contiene(self, eid: int) -> bool:
        return self.tipo_slot_de(eid) is not None

    def vacia(self) -> bool:
        return self.suelo is None and self.bot is None and not self.resto
