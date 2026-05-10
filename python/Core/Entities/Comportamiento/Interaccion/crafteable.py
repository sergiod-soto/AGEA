# crafteable.py — filtra y construye la Receta
from abc import abstractmethod
from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Comportamiento.Interaccion._receta import Receta
from Core.Entities.Elementos.elemento import Elemento


class Crafteable(Interaccion):
    def __init__(self, receta_para: Receta, **kwargs):
        super().__init__(**kwargs)
        self.receta = receta_para
        for ingrediente in self.receta.ingredientes:
            ingrediente.incluir_en_receta(self.receta)

    def get_receta_para(self) -> list:
        return self.receta.ingredientes + self.receta.condiciones + self.receta.acciones

    def ejecutar(self) -> None:
        for accion in self.receta.acciones:
            accion.ejecutar()

    @abstractmethod
    def craftear(self, elementos: list[Elemento]): ...
