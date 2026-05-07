# ingrediente.py — TYPE_CHECKING rompe el ciclo en runtime
from __future__ import annotations
from typing import TYPE_CHECKING

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.elemento import Elemento

if TYPE_CHECKING:
    from Core.Entities.Comportamiento.Interaccion.receta import Receta

class Ingrediente(Interaccion):
    def __init__(self, recetas_de: dict[str, Receta] = None, **kwargs):
        super().__init__(**kwargs)
        self.recetas_de: dict[str, Receta] = recetas_de or {}
        Elemento.mundo.bus.suscribir(f"manipulado_{id(self)}", self.on_manipulado)

    def on_manipulado(self) -> None:
        for receta in self.recetas_de.values():
            if receta.condiciones_cumplidas():
                Elemento.mundo.bus.emitir("craftear", receta)

    def incluir_en_receta(self, receta: Receta) -> None:
        if receta.nombre in self.recetas_de:
            return
        self.recetas_de[receta.nombre] = receta

    def parte_de_que_recetas(self) -> dict[str, Receta]:
        return self.recetas_de

    def eliminar(self) -> None:
        Elemento.mundo.bus.desuscribir(f"manipulado_{id(self)}", self.on_manipulado)