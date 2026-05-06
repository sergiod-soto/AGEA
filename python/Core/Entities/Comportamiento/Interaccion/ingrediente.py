from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.crafteable import Crafteable
from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.elemento import Elemento


class Ingrediente(Interaccion):
    """
    Forma parte de una receta.

    Parametros:

    - recetas: dict[str, Crafteable]
    """

    def __init__(self, recetas: dict[str, Crafteable],**kwargs):
        super().__init__(**kwargs)
        self.recetas = recetas

        for nombre, crafteable in recetas.items():
            self.incluir_en_receta((nombre, crafteable))

        Elemento.mundo.bus.suscribir(f"manipulado_{id(self)}", self.on_manipulado)

    def on_manipulado(self) -> None:
        for crafteable in self.recetas.values():
            if crafteable.condiciones_cumplidas():
                Elemento.mundo.bus.emitir("craftear", crafteable)

    def incluir_en_receta(self, receta: tuple[str, Crafteable]) -> None:
        """Incluye el elemento en 'parte_de_que_recetas()'"""

        if self.recetas.get(receta[0]) is not None:
            return

        self.recetas[receta[0]] = receta[1]

    def parte_de_que_recetas(self) -> dict[str, Crafteable]:
        """Retorna de que recetas este Elemento forma parte"""
        return self.recetas

    def eliminar(self) -> None:
        Elemento.mundo.bus.desuscribir(f"manipulado_{id(self)}", self.on_manipulado)
