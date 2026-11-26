# Core/Entities/Elementos/Complejos/Lago/Lago.py

from __future__ import annotations
from typing import Optional
from Core.Entities.Comportamiento.comportamiento import Comportamiento as C
from Core.Entities.Elementos.Complejos.elemento_complejo import Elemento_Complejo

comportamientos = C.declarar_comportamientos()


class Lago(Elemento_Complejo, comportamientos):
    """
    Representa una cuenca lacustre en el grafo hidrográfico.
    Acumula agua hasta una cota crítica X (capacidad_maxima).
    Por debajo de X retiene agua (caudal_salida = 0) e inunda celdas
    por orden de cota batimétrica.
    Al superar X, desborda por su punto de fuga más bajo a través de
    su río emisario (desagua_en_rio).
    """

    def __init__(
        self,
        id_elemento: int = 0,
        nace_de_rio: Optional[int] = None,
        desagua_en_rio: Optional[int] = None,
        capacidad_maxima: float = 0.0,
        fondo: float = 0.0,
        area: int = 0,
        volumen: float = 0.0,
        nivel_actual: Optional[float] = None,
        celdas_cuenca: Optional[list[tuple[int, int, float]]] = None,
        punto_desborde: Optional[tuple[int, int]] = None,
        **kwargs,
    ):
        super().__init__(tipo=Lago, capa=-1, id_elemento=id_elemento, **kwargs)
        self.id_lago = id_elemento
        self.nace_de_rio = nace_de_rio
        self.desagua_en_rio = desagua_en_rio
        self.capacidad_maxima = float(capacidad_maxima)
        self.fondo = float(fondo)
        self.area = int(area)
        self.volumen = float(volumen)
        self.nivel_actual = float(nivel_actual if nivel_actual is not None else fondo)
        self.celdas_cuenca = list(celdas_cuenca) if celdas_cuenca is not None else []
        self.punto_desborde = (
            tuple(punto_desborde) if punto_desborde is not None else None
        )
        self.celdas_inundadas: set[tuple[int, int]] = set()
        self.caudal_entrada = 0.0
        self.caudal_salida = 0.0

    def serializar(self) -> dict:
        datos = super().serializar()
        desborde_ref = (
            list(self.punto_desborde) if self.punto_desborde is not None else None
        )
        datos["lago"] = {
            "id_lago": self.id_lago,
            "nace_de_rio": self.nace_de_rio,
            "desagua_en_rio": self.desagua_en_rio,
            "capacidad_maxima": self.capacidad_maxima,
            "fondo": self.fondo,
            "area": self.area,
            "volumen": self.volumen,
            "nivel_actual": self.nivel_actual,
            "celdas_cuenca": [
                [x, y, float(e)] for x, y, e in self.celdas_cuenca
            ],
            "celdas_inundadas": [list(c) for c in self.celdas_inundadas],
            "punto_desborde": desborde_ref,
            "caudal_entrada": self.caudal_entrada,
            "caudal_salida": self.caudal_salida,
        }
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        lago_data = data.get("lago", {})
        self.id_lago = lago_data.get("id_lago", self.id_elemento)
        self.nace_de_rio = lago_data.get("nace_de_rio")
        self.desagua_en_rio = lago_data.get("desagua_en_rio")
        self.capacidad_maxima = float(lago_data.get("capacidad_maxima", 0.0))
        self.fondo = float(lago_data.get("fondo", 0.0))
        self.area = int(lago_data.get("area", 0))
        self.volumen = float(lago_data.get("volumen", 0.0))
        self.nivel_actual = float(lago_data.get("nivel_actual", self.fondo))
        self.celdas_cuenca = [
            (int(c[0]), int(c[1]), float(c[2]))
            for c in lago_data.get("celdas_cuenca", [])
        ]
        self.celdas_inundadas = {
            (int(c[0]), int(c[1])) for c in lago_data.get("celdas_inundadas", [])
        }
        p_des = lago_data.get("punto_desborde")
        self.punto_desborde = (int(p_des[0]), int(p_des[1])) if p_des else None
        self.caudal_entrada = float(lago_data.get("caudal_entrada", 0.0))
        self.caudal_salida = float(lago_data.get("caudal_salida", 0.0))
