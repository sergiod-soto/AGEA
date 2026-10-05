from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class CondicionUmbralHumedad(Condicion):
    def __init__(self, umbral: float, por_debajo: bool, **kwargs):
        super().__init__(**kwargs)
        self.umbral = umbral
        self.por_debajo = por_debajo

    def evaluar(self, propietario, ctx) -> bool:
        # propietario.casilla ya existe en Suelo -- no hace falta
        # guardar la posición en la propia Condicion.
        celda = ctx.get_atmosfera(*propietario.casilla)
        return (celda.humedad_absoluta.valor < self.umbral) == self.por_debajo

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return ["umbral", "por_debajo"]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return "Compara la humedad absoluta de la celda de atmósfera propia contra un umbral."
