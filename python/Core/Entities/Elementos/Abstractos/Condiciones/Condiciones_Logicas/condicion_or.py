# Core/Entities/Elementos/Abstractos/Condiciones/Condiciones_Logicas/condicion_or.py


from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class CondicionOr(Condicion):
    """
    Se cumple si AL MENOS UNA condición en 'condiciones' se cumple.
    """

    def __init__(self, condiciones: list[Condicion], **kwargs):
        super().__init__(**kwargs)
        self.condiciones = condiciones

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["condiciones"] = [c.serializar() for c in self.condiciones]
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        # Import diferido: evita el ciclo con el registry.
        from Core.Entities.Elementos.registry import reconstruir_elemento

        super().deserializar(data, mundo)
        self.condiciones = [reconstruir_elemento(d, mundo) for d in data["condiciones"]]

    def evaluar(self, propietario, ctx) -> bool:
        return any(c.evaluar(propietario, ctx) for c in self.condiciones)
