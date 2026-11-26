# Core/Entities/Elementos/Complejos/Oceano/Oceano.py

from __future__ import annotations
from typing import Optional
from Core.Entities.Comportamiento.comportamiento import Comportamiento as C
from Core.Entities.Elementos.Complejos.elemento_complejo import Elemento_Complejo

comportamientos = C.declarar_comportamientos()


class Oceano(Elemento_Complejo, comportamientos):
    """
    Representa la masa oceánica global receptora de las desembocaduras fluviales.
    Actúa como sumidero final para ríos que alcanzan el mar.
    """

    def __init__(
        self,
        id_elemento: int = 0,
        nivel_mar: float = 0.0,
        volumen_recibido: float = 0.0,
        celdas_costa: Optional[set[tuple[int, int]]] = None,
        **kwargs,
    ):
        super().__init__(tipo=Oceano, capa=-1, id_elemento=id_elemento, **kwargs)
        self.nivel_mar = float(nivel_mar)
        self.volumen_recibido = float(volumen_recibido)
        self.celdas_costa = set(celdas_costa) if celdas_costa is not None else set()

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["oceano"] = {
            "id_elemento": self.id_elemento,
            "nivel_mar": self.nivel_mar,
            "volumen_recibido": self.volumen_recibido,
            "celdas_costa": [list(c) for c in self.celdas_costa],
        }
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        oc_data = data.get("oceano", {})
        self.nivel_mar = float(oc_data.get("nivel_mar", 0.0))
        self.volumen_recibido = float(oc_data.get("volumen_recibido", 0.0))
        self.celdas_costa = {
            (int(c[0]), int(c[1])) for c in oc_data.get("celdas_costa", [])
        }
