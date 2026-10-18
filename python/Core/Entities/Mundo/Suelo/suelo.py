# Core/Entities/Mundo/Suelo/suelo.py

from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto


class Suelo(Elemento_Abstracto):
    """
    Base de cada casilla. En la física solo hace dos cosas: convierte la
    radiación solar entrante en calor (tasa) y fija la masa térmica del
    suelo (inercia). La celda de atmósfera promedia ambos valores de sus
    casillas y con ellos calienta su temperatura de suelo, que a su vez
    calienta el aire.

    - tasa_conversion_radiacion_calor: en [0, 100].
    - inercia_termica: J/(m²·K), debe ser > 0. Es SOLO la masa del suelo;
      el aire de la celda se cuenta aparte (C_AIRE, en temperatura_atmosferica).
    """

    def __init__(
        self,
        casilla: tuple[int, int],
        id_elemento,
        tipo,
        tasa_conversion_radiacion_calor,
        inercia_termica,
        **kwargs,
    ):
        # Se valida antes de construir: con valores inválidos el error
        # saltaría en el primer tick de atmósfera, lejos de su origen.
        self._validar(tasa_conversion_radiacion_calor, inercia_termica)
        super().__init__(
            tipo=tipo,
            id_elemento=id_elemento,
            **kwargs,
        )
        self.casilla = casilla
        self.tasa_conversion_radiacion_calor = tasa_conversion_radiacion_calor
        self.inercia_termica = inercia_termica

    @staticmethod
    def _validar(tasa, inercia) -> None:
        # `not (...)` en vez de `<`/`>` para rechazar también NaN.
        if not 0 <= tasa <= 100:
            raise ValueError(
                f"tasa_conversion_radiacion_calor debe estar en [0, 100]; recibido {tasa!r}"
            )
        if not inercia > 0:
            raise ValueError(f"inercia_termica debe ser > 0; recibido {inercia!r}")

    # --- Hooks por campo: conversión de formato ---

    def serializar_casilla(self) -> dict:
        """Formato {"x":, "y":}: el que Unity espera para 'casilla'."""
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
        El suelo es la base visual imprescindible: IGNORA `incluir` y manda
        siempre todo (pasando None a la cadena super()).
        """
        datos = super().representar(None)
        datos["elemento"]["casilla"] = self.serializar_casilla()
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        self._validar(data["tasa_conversion_radiacion_calor"], data["inercia_termica"])
        self.deserializar_casilla(data["casilla"])
        self.tasa_conversion_radiacion_calor = data["tasa_conversion_radiacion_calor"]
        self.inercia_termica = data["inercia_termica"]
