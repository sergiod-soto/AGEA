# Core/Entities/Elementos/Abstractos/Condiciones/condicion_or.py
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion
from Core.Entities.entity import Modos


class CondicionOr(Condicion):
    """
    Se cumple si AL MENOS UNA condición en 'condiciones' se cumple.
    """

    def __init__(self, condiciones: list[Condicion], **kwargs):
        super().__init__(**kwargs)
        self.condiciones = condiciones

    def serialize_condiciones(self) -> list[dict]:
        return [c.serializar(modo=Modos.guardado) for c in self.condiciones]

    def deserialize_condiciones(self, valor: list[dict]) -> None:
        from Core.Entities.Elementos.registry import reconstruir_elemento

        self.condiciones = [reconstruir_elemento(d, self.mundo) for d in valor]

    def evaluar(self, propietario, ctx) -> bool:
        # any() ya hace cortocircuito: se detiene en la primera True.
        return any(c.evaluar(propietario, ctx) for c in self.condiciones)
