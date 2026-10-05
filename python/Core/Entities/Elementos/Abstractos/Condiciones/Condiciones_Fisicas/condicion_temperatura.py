from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class CondicionTemperatura(Condicion):
    def __init__(self, umbral: float, por_debajo: bool, **kwargs):
        super().__init__(**kwargs)
        self.umbral = umbral
        self.por_debajo = por_debajo

    def evaluar(self, propietario, ctx) -> bool:
        return (propietario.temperatura_propia <= self.umbral) == self.por_debajo
