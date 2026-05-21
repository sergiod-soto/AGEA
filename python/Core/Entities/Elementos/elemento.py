from abc import ABC

from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Mundo.mundo import Mundo


class Elemento(Comportamiento):
    """
    Clase base de las cosas que son un elemento, ya sea simple, complejo o abstracto.


    Los elementos existen en el mundo, pueden o no moverse a cambio de energia y
    pueden interactuar entre ellos en funcion de su presencia en las proximidades
    """

    mundo: Mundo = None

    def __init__(self, tipo: type, capa: int, **kwargs):
        super().__init__(**kwargs)

        self.capa = capa
        self.tipo = tipo

    def _get_comportamientos(self) -> list[type]:
        return [
            c
            for c in self.__class__.__mro__
            if c not in (Elemento, ABC, object) and issubclass(c, Comportamiento)
        ]

    def _serializar_propios(self) -> dict:
        atributos_comportamientos = set()
        for c in self._get_comportamientos():
            for k in c.__dict__:  # atributos definidos en la clase, no instancia
                atributos_comportamientos.add(k)

        return {
            k: v
            for k, v in vars(self).items()
            if not k.startswith("_") and k not in atributos_comportamientos
        }

    def serializar(self) -> dict:
        return {
            **self._serializar_propios(),
            "comportamientos": {
                c.__name__: c.serializar(self) for c in self._get_comportamientos()
            },
        }

    def deserializar(self, data: dict):
        # Deserializa atributos propios del elemento
        atributos_comportamientos = {
            attr for c in self._get_comportamientos() for attr in c.atributos
        }
        for k, v in data.items():
            if (
                k not in ("__clase__", "comportamientos")
                and k not in atributos_comportamientos
            ):
                setattr(self, k, v)

        # Delega a cada comportamiento su deserialización
        for c in self._get_comportamientos():
            if c.__name__ in data["comportamientos"]:
                c.deserializar(self, data["comportamientos"][c.__name__])

    def eliminar(self):
        # Delega a cada comportamiento su limpieza
        for c in self._get_comportamientos():
            c.eliminar(self)

        # Limpia atributos propios
        atributos_comportamientos = {
            attr for c in self._get_comportamientos() for attr in c.atributos
        }
        for k in list(vars(self).keys()):
            if k not in atributos_comportamientos and not k.startswith("_"):
                setattr(self, k, None)

        # Avisa al mundo para que elimine la referencia
        self._mundo.eliminar_elemento(self)
