# receta.py — no importa Ingrediente
from Core.Entities.Elementos.Abstractos.Acciones.accion import Accion
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class Receta:
    def __init__(
        self,
        nombre: str,
        ingredientes: list,
        condiciones: list[Condicion],
        acciones: list[Accion],
    ):
        self.nombre = nombre
        self.ingredientes = ingredientes
        self.condiciones = condiciones
        self.acciones = acciones

    def condiciones_cumplidas(self) -> bool:
        return all(c.evaluar() for c in self.condiciones)
