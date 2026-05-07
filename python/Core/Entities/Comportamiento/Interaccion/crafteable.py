from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.ingrediente import Ingrediente
from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.Abstractos.Acciones.accion import Accion
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion
from Core.Entities.Elementos.elemento import Elemento


class Crafteable(Interaccion):
    """
    Parametros:

    - receta_para: tuple[str, list[Elemento]]

    Metodos abstractos:

    - craftear(self, elementos: list[Elemento])
    """

    def __init__(self, receta_para: tuple[str, list[Elemento]], **kwargs):
        super().__init__(**kwargs)
        self.nombre = receta_para[0]
        self.receta_para = receta_para[1]
        self.ingredientes = [e for e in self.receta_para if isinstance(e, Ingrediente)]
        self.condiciones = [e for e in self.receta_para if isinstance(e, Condicion)]
        self.acciones = [e for e in self.receta_para if isinstance(e, Accion)]
        for ingrediente in self.ingredientes:
            ingrediente.incluir_en_receta((self.nombre, self))

    def get_receta_para(self) -> list[Elemento]:
        """
        Consulta que necesita para ser creado
        """
        return self.receta_para

    def condiciones_cumplidas(self) -> bool:
        return all(c.evaluar() for c in self.condiciones)

    def ejecutar(self) -> None:
        for accion in self.acciones:
            accion.ejecutar()

    @abstractmethod
    def craftear(self, elementos: list[Elemento]): ...
