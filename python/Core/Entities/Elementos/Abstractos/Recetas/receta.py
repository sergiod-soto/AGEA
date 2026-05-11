# receta.py — no importa Ingrediente
from typing import Callable

from Core.Entities.Elementos.Abstractos.Acciones.accion import Accion
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion
from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto
from Core.Entities.Elementos.elemento import Elemento


class Receta(Elemento_Abstracto):

    # Diccionario de los elementos que potencialmente se van a usar
    # en una receta.
    #
    # La clave es la receta y el valor es otro diccionario.
    #
    # En este segundo diccionario, la clave es
    # el id de la accion y el valor una lista con los ingredientes

    registro_ingredientes_recetas = {
        "MASA_PAN": {},
    }

    def __init__(
        self,
        nombre: str,
        ingredientes: list,  # para evitar dependencia circular, ¡NO! decir que es de Ingrediente
        condiciones: list[Condicion],
        accion: Accion,
        resultado: Callable,
        **kwargs,
    ):
        super().__init__(Receta, **kwargs)
        self.nombre = nombre
        self.ingredientes = ingredientes
        self.condiciones = condiciones
        self.accion = accion
        self.resultado = resultado

    def _on_accion(self, elementos: list[Elemento]) -> None:
        if self._ingredientes_presentes(elementos) and self._condiciones_cumplidas(
            elementos
        ):
            self.resultado(elementos)

    def _ingredientes_presentes(self, elementos: list[Elemento]) -> bool:
        return all(
            any(isinstance(e, tipo) for e in elementos) for tipo in self.ingredientes
        )

    def _condiciones_cumplidas(self, elementos: list[Elemento]) -> bool:
        return all(c.evaluar(elementos) for c in self.condiciones)
