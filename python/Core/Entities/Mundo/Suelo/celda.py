# Core/Entities/Mundo/Celda/celda.py
"""
Celda: contenedor de los elementos que ocupan una posición del mundo.

Tres slots, igual que usaba Logica_Mundo:
- suelo: como mucho un elemento (id) de tipo suelo.
- bot:   como mucho un elemento (id) de tipo bot.
- resto: cualquier cantidad de elementos (ids) de cualquier otro tipo.

Todo se guarda por id (uint64), nunca por objeto: el objeto real vive en
Mundo.elementos. Es intencional -- una única fuente de verdad para el
estado del elemento, y hace trivial serializar la celda (solo ids).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from numpy import uint64


@dataclass
class Celda:
    suelo: Optional[uint64] = None
    bot: Optional[uint64] = None
    resto: list[uint64] = field(default_factory=list)

    def put_elemento(self, eid: uint64, tipo_slot: str) -> None:
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

    def tipo_slot_de(self, eid: uint64) -> Optional[str]:
        """En qué slot está 'eid' ('suelo'/'bot'/'resto'), o None si no
        está en esta celda."""
        if self.suelo == eid:
            return "suelo"
        if self.bot == eid:
            return "bot"
        if eid in self.resto:
            return "resto"
        return None

    def remove_elemento(self, eid: uint64) -> bool:
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

    def contiene(self, eid: uint64) -> bool:
        return self.tipo_slot_de(eid) is not None

    def vacia(self) -> bool:
        return self.suelo is None and self.bot is None and not self.resto
