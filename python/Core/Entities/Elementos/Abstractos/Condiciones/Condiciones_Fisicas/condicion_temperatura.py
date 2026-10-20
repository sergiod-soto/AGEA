# Core/Entities/Elementos/Abstractos/Condiciones/Condiciones_Fisicas/condicion_temperatura.py

from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class CondicionTemperatura(Condicion):
    """
    Compara la temperatura del SUELO (K) de la celda de atmósfera del
    propietario con un umbral en K. OJO: es la media de las casillas de la
    celda (ATMOSFERA_ESCALA² casillas), no la de una casilla concreta.
    por_debajo=True se cumple si T <= umbral; por_debajo=False, si T > umbral.
    """

    CAMPOS = ("umbral", "por_debajo")

    def __init__(self, umbral: float, por_debajo: bool, **kwargs):
        super().__init__(**kwargs)
        self.umbral = umbral
        self.por_debajo = por_debajo

    def evaluar(self, propietario, ctx) -> bool:
        celda = ctx.get_atmosfera(*propietario.casilla)
        if celda is None:
            # Fatal, igual que CondicionUmbralHumedad y Acuoso.
            raise RuntimeError(
                f"CondicionTemperatura en {propietario.casilla}: sin Celda_Atmosfera."
            )
        return (celda.temperatura.valor_suelo <= self.umbral) == self.por_debajo