# Core/Entities/Elementos/Abstractos/Condiciones/condicion_and.py
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class CondicionAnd(Condicion):
    """Se cumple si TODAS las condiciones en 'condiciones' se cumplen.
    Permite recombinar condiciones ya existentes (humedad, vecino
    cercano, tick objetivo...) sin escribir una clase ad-hoc por cada
    combinación nueva que haga falta."""

    def __init__(self, condiciones: list[Condicion], **kwargs):
        super().__init__(**kwargs)
        self.condiciones = condiciones

    def serializar(self) -> list[dict]:
        return [c.serializar() for c in self.condiciones]

    def representar(self):
        return self.serializar()

    def deserializar(self, valor: list[dict]) -> None:
        from Core.Entities.Elementos.registry import reconstruir_elemento

        self.condiciones = [reconstruir_elemento(d, self.mundo) for d in valor]

    def evaluar(self, propietario, ctx) -> bool:
        return all(c.evaluar(propietario, ctx) for c in self.condiciones)
