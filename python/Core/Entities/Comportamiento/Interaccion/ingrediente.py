# ingrediente.py — TYPE_CHECKING rompe el ciclo en runtime
from __future__ import annotations

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.Abstractos.Recetas.receta import Receta
from Core.Entities.Elementos.elemento import Elemento


class Ingrediente(Interaccion):
    """
    Parametros:

    - recetas_de: list[Receta]

    Metodos abstractos:

    -
    """
    
    REQUIERE = {"recetas_de: list[Receta]"}
    ABSTRACTOS = {}

    def __init__(self, recetas_de: list[Receta], **kwargs):
        super().__init__(**kwargs)
        self.recetas_de: list[Receta] = recetas_de


    def incluir_en_receta(self, receta: Receta) -> None:
        if receta.nombre in self.recetas_de:
            return
        self.recetas_de[receta.nombre] = receta

    def parte_de_que_recetas(self) -> dict[str, Receta]:
        return self.recetas_de
