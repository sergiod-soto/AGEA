# Core/Entities/Elementos/Complejos/Rio/Rio.py

from __future__ import annotations
from typing import Optional
from Core.Entities.Comportamiento.comportamiento import Comportamiento as C
from Core.Entities.Elementos.Complejos.elemento_complejo import Elemento_Complejo

comportamientos = C.declarar_comportamientos()


class Rio(Elemento_Complejo, comportamientos):
    """
    Representa una sección/tramo de río en el DAG hidrográfico.
    Agrupa el camino de celdas desde su nacimiento (manantial/lago/confluencia)
    hasta su desembocadura (mar/lago/confluencia/seca), así como anillos
    de ensanchamiento de su cauce.
    """

    def __init__(
        self,
        id_elemento: int = 0,
        nace_de: tuple = ("manantial", None),
        muere_en: tuple = ("mar", None),
        camino: Optional[list[tuple[int, int]]] = None,
        ancho_celdas: Optional[list[tuple[int, int]]] = None,
        volumen: float = 0.0,
        capacidad_base: float = 1000.0,
        activo: bool = True,
        **kwargs,
    ):
        super().__init__(tipo=Rio, capa=-1, id_elemento=id_elemento, **kwargs)
        self.id_rio = id_elemento
        self.nace_de = (
            tuple(nace_de)
            if isinstance(nace_de, (list, tuple))
            else ("manantial", None)
        )
        self.muere_en = (
            tuple(muere_en)
            if isinstance(muere_en, (list, tuple))
            else ("mar", None)
        )
        self.camino = list(camino) if camino is not None else []
        self.ancho_celdas = list(ancho_celdas) if ancho_celdas is not None else []
        self.volumen = float(volumen)
        self.capacidad_base = float(capacidad_base)
        self.caudal_entrada = 0.0
        self.caudal_salida = 0.0
        self.activo = bool(activo)

    def serializar(self) -> dict:
        datos = super().serializar()
        nace_ref = self.nace_de[1]
        if isinstance(nace_ref, (list, tuple)):
            nace_ref = list(nace_ref)
        muere_ref = self.muere_en[1]
        if isinstance(muere_ref, (list, tuple)):
            muere_ref = list(muere_ref)

        datos["rio"] = {
            "id_rio": self.id_rio,
            "nace_de": [self.nace_de[0], nace_ref],
            "muere_en": [self.muere_en[0], muere_ref],
            "camino": [list(c) for c in self.camino],
            "ancho_celdas": [list(c) for c in self.ancho_celdas],
            "volumen": self.volumen,
            "capacidad_base": self.capacidad_base,
            "caudal_entrada": self.caudal_entrada,
            "caudal_salida": self.caudal_salida,
            "activo": self.activo,
        }
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        rio_data = data.get("rio", {})
        self.id_rio = rio_data.get("id_rio", self.id_elemento)
        nace_raw = rio_data.get("nace_de", ["manantial", None])
        if isinstance(nace_raw, (list, tuple)) and len(nace_raw) == 2:
            ref = nace_raw[1]
            if isinstance(ref, list):
                ref = tuple(ref)
            self.nace_de = (nace_raw[0], ref)
        else:
            self.nace_de = ("manantial", None)

        muere_raw = rio_data.get("muere_en", ["mar", None])
        if isinstance(muere_raw, (list, tuple)) and len(muere_raw) == 2:
            ref = muere_raw[1]
            if isinstance(ref, list):
                ref = tuple(ref)
            self.muere_en = (muere_raw[0], ref)
        else:
            self.muere_en = ("mar", None)

        self.camino = [tuple(c) for c in rio_data.get("camino", [])]
        self.ancho_celdas = [tuple(c) for c in rio_data.get("ancho_celdas", [])]
        self.volumen = float(rio_data.get("volumen", 0.0))
        self.capacidad_base = float(rio_data.get("capacidad_base", 1000.0))
        self.caudal_entrada = float(rio_data.get("caudal_entrada", 0.0))
        self.caudal_salida = float(rio_data.get("caudal_salida", 0.0))
        self.activo = bool(rio_data.get("activo", True))
