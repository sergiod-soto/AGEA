# Core/Entities/Elementos/Abstractos/Condiciones/condicion.py

from abc import abstractmethod

from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto


class Condicion(Elemento_Abstracto):
    """
    Base de las condiciones serializables. Se evalúan SIEMPRE dentro del tick
    del Sector (Transformable.tick_comportamiento): mismo código en local y en
    AWS, por eso no hay modos. 'propietario' y 'ctx' se pasan en cada llamada
    a evaluar(), nunca se guardan como campo.

    Serialización: un Elemento NO serializa sus campos solo; cada subtipo
    declara en CAMPOS los atributos planos (int, float, bool, str) que debe
    guardar. Las condiciones compuestas (And/Or) añaden las anidadas a mano.

    Cada subtipo concreto debe estar en Core/Entities/Elementos/registry.
    """

    # Atributos planos a serializar. Cada subtipo lo sobrescribe.
    CAMPOS: tuple[str, ...] = ()

    def __init__(self, id_elemento=None, **kwargs):
        super().__init__(tipo=type(self), id_elemento=id_elemento, **kwargs)

    @abstractmethod
    def evaluar(self, propietario, ctx) -> bool: ...

    def serializar_id_elemento(self):
        # Una condición no es un elemento del mundo: no tiene id propio. Su
        # identidad estable es (id del dueño, nombre en dict_transformable).
        return None

    def serializar(self) -> dict:
        datos = super().serializar()
        for campo in self.CAMPOS:
            datos[campo] = getattr(self, campo)
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        for campo in self.CAMPOS:
            setattr(self, campo, data[campo])
