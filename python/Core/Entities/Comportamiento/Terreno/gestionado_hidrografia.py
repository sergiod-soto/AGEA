# Core/Entities/Comportamiento/Terreno/gestionado_hidrografia.py

from Core.Entities.Comportamiento.Terreno.terreno import Terreno


class GestionadoHidrografia(Terreno):
    """
    Comportamiento que marca una entidad o masa de agua como gestionada
    de forma agregada por el sistema hidrográfico (red fluvial de ríos y lagos).
    Inhibe la evaporación y dispersión individual a nivel de celda o sector.
    """

    REQUIERE = {}
    ABSTRACTOS = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gestionado_por_hidrografia = True

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {
            "gestionado_hidrografia": {}
        }
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {
                "gestionado_hidrografia": {}
            }
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        self.gestionado_por_hidrografia = True
