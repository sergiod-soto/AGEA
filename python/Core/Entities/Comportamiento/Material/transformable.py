from abc import abstractmethod
import inspect
from typing import Callable

from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class Transformable(Material):
    """
    Elemento que, al darse una condicion, es cambiado por otro:

    Puede ser reversible, como agua -> hielo -> agua

    El Callable es la funcion que transforma al Elemento

    Parametros:

    - dict_transformable: dict[Condicion, Callable]

    Metodos abstractos:

    -
    """

    REQUIERE = {"dict_transformable: dict[Condicion, Callable]"}
    ABSTRACTOS = {}

    def __init__(self, dict_transformable: dict, **kwargs):
        super().__init__(**kwargs)
        self.dict_transformable = dict_transformable

        # Cacheado una sola vez en construcción: la firma de un
        # callable no cambia en caliente, y llamar a
        # inspect.signature() en cada tick sería trabajo repetido e
        # innecesario para un resultado ya conocido desde el principio.
        self._acepta_ctx: dict[Condicion, bool] = {
            condicion: "ctx" in inspect.signature(callable_).parameters
            for condicion, callable_ in dict_transformable.items()
        }

    def tick(self, pos: tuple[int, int], ctx) -> None:
        for condicion, callable_transformacion in self.dict_transformable.items():
            if condicion.modo is not Condicion.Modo.LOCAL:
                continue  # las DISTRIBUIDAS se disparan solas vía bus
            if condicion.evaluar():
                if self._acepta_ctx[condicion]:
                    callable_transformacion(ctx)
                else:
                    callable_transformacion()
                return  # una transformación por tick

    def get_condiciones(self) -> list[Condicion]:
        return list(self.dict_transformable.keys())

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "dict_transformable",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento puede transformarse en otro (ser eliminado y crear otro nuevo)
al cumplirse ciertas condiciones.

Atributos:
\tdict_transformable: dict[Condicion, Callable]

Métodos:
\tget_condiciones(self) -> list[Condicion]
\t--------------------------------------
\tConsulta el diccionario de qué transformaciones convierten el Elemento en cual.
        """
