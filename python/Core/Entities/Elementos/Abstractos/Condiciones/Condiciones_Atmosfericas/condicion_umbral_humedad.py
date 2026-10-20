# Core/Entities/Elementos/Abstractos/Condiciones/Condiciones_Atmosfericas/condicion_umbral_humedad.py

from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class CondicionUmbralHumedad(Condicion):

    CAMPOS = ("umbral", "por_debajo")

    def __init__(self, umbral: float, por_debajo: bool, **kwargs):
        super().__init__(**kwargs)
        self.umbral = umbral
        self.por_debajo = por_debajo

    def evaluar(self, propietario, ctx) -> bool:
        # Humedad RELATIVA (0-100 %): los umbrales de los suelos (5, 10) son
        # porcentajes. La absoluta está en kg/m³ y nunca se acerca a esos valores.
        celda = ctx.get_atmosfera(*propietario.casilla)
        if celda is None:
            # Fatal, igual que Acuoso: un suelo sin celda de atmósfera es un
            # mundo mal generado o un LoadState incompleto.
            raise RuntimeError(
                f"CondicionUmbralHumedad en {propietario.casilla}: sin Celda_Atmosfera."
            )
        return (celda.humedad_relativa.valor < self.umbral) == self.por_debajo

    @classmethod
    def ayuda_creacion(cls) -> str:
        return (
            "Compara la humedad RELATIVA (%) de la celda de atmósfera propia "
            "contra un umbral (por_debajo=True: se cumple si es menor)."
        )

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return ["umbral", "por_debajo"]
