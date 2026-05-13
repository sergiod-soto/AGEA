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
        #
        # para evitar dependencia circular, ¡NO! decir que es de Ingrediente.
        ingredientes: list,
        #
        # lugar donde tiene lugar la Receta
        donde,
        #
        # puede que alguna de las condiciones sea el trigger.
        condiciones: list[Condicion],
        #
        # accion que hace de trigger. puede no tener.
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

    def _on_accion(
        self,
        objetivo: Elemento,  # el objetivo puede ser un recipiente, terreno, etc
        elementos: list[Elemento],
    ) -> None:
        if self._ingredientes_presentes(
            objetivo, elementos
        ) and self._condiciones_cumplidas(elementos):
            if self.resultado is None:
                raise Exception(
                    f"[''RESULTADO'' is None] en accion: {str(self.accion.nombre)} en objetivo tipo: {str(objetivo.tipo)}"
                )
            # Se ejecuta la funcion resultado
            self.resultado(
                objetivo,
                self.registro_ingredientes_recetas[self.accion.nombre][id(objetivo)],
            )

    def _ingredientes_presentes(
        self,
        objetivo: Elemento,
        elementos: list[Elemento],
    ) -> bool:
        """
        Compruebo la presencia de todos los ingredientes necesarios y
        los guardo en el registro. Se guardan todos los que casan
        con la receta, esten duplicados o no.
        """

        ingredientes_a_usar = []
        for tipo in self.ingredientes:
            for e in elementos:
                if isinstance(e, tipo):
                    ingredientes_a_usar.append(e)
                    encontrado = True
                    continue
            if encontrado == False:
                return False
        self.registro_ingredientes_recetas[self.accion.nombre][
            id(objetivo)
        ] = ingredientes_a_usar

        return True

    def _condiciones_cumplidas(self, elementos: list[Elemento]) -> bool:
        return all(c.evaluar(elementos) for c in self.condiciones)
