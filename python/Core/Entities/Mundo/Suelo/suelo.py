# Core/Entities/Mundo/Suelo/suelo.py

from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto


class Suelo(Elemento_Abstracto):

    def __init__(
        self,
        casilla: tuple[int, int],
        id_elemento,
        tipo,
        tasa_conversion_radiacion_calor,
        inercia_termica,
        **kwargs,
    ):
        super().__init__(
            tipo=tipo,
            id_elemento=id_elemento,
            **kwargs,
        )
        self.casilla = casilla
        self.tasa_conversion_radiacion_calor = tasa_conversion_radiacion_calor
        self.inercia_termica = inercia_termica

    # --- Hooks por campo (se mantienen): conversión de formato ---

    def serializar_casilla(self) -> dict:
        """
        Formato {"x":, "y":}: es el que Unity espera para 'casilla' en
        cualquier tipo de elemento (mismo formato que Elemento_Simple).
        """
        x, y = self.casilla
        return {"x": x, "y": y}

    def deserializar_casilla(self, value: dict) -> None:
        self.casilla = (value["x"], value["y"])

    # --- Cadena serializar / representar / deserializar ---

    def serializar(self) -> dict:
        datos = super().serializar()
        datos.update(
            {
                "casilla": self.serializar_casilla(),
                "tasa_conversion_radiacion_calor": self.tasa_conversion_radiacion_calor,
                "inercia_termica": self.inercia_termica,
            }
        )
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """
        El suelo es la base visual imprescindible, no un dato opcional:
        IGNORA `incluir` y manda siempre todo (decisión explícita que ya
        tenía representar_suelo). Se consigue pasando None ("todo") a la
        cadena super(), así los comportamientos tampoco se filtran.
        """
        datos = super().representar(None)
        datos["elemento"]["casilla"] = self.serializar_casilla()
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        self.deserializar_casilla(data["casilla"])
        self.tasa_conversion_radiacion_calor = data["tasa_conversion_radiacion_calor"]
        self.inercia_termica = data["inercia_termica"]
