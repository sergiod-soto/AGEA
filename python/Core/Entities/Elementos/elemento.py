# Core/Entities/Elemento/elemento.py
from abc import ABC
from typing import TYPE_CHECKING
from numpy import uint64
from Core.Entities.Comportamiento.comportamiento import Comportamiento

if TYPE_CHECKING:
    from Core.Entities.Mundo.mundo import Mundo


class Elemento(ABC, Comportamiento):
    """
    Clase base de las cosas que son un elemento, ya sea simple, complejo o abstracto.

    Los elementos existen en el mundo, pueden o no moverse a cambio de energia y
    pueden interactuar entre ellos en funcion de su presencia en las proximidades
    """

    def __init__(
        self,
        tipo: type,
        capa: int,
        id: uint64,
        fuerza_sector_activo: bool,
        fuerza_vecinos_activos: bool,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.capa = capa
        self.tipo = tipo
        self.id = id
        self.fuerza_sector_activo = fuerza_sector_activo
        self.fuerza_vecinos_activos = fuerza_vecinos_activos
        self.excluyente_en_celda = False
        self.mundo: Mundo | None = None

    def _get_comportamientos(self) -> list[type]:
        return [
            c
            for c in self.__class__.__mro__
            if c not in (Elemento, ABC, object) and issubclass(c, Comportamiento)
        ]

    def _atributos_de_comportamientos(self) -> set[str]:
        """
        Unión de los nombres de atributo que declara el __init__ PROPIO
        (no heredado) de cada comportamiento presente en este elemento.

        Reusa Comportamiento._params_propios(cls) — misma introspección
        que ya usan Comportamiento.anhadir()/quitar(): mira la firma de
        cls.__init__ tal como está definida en esa clase concreta (no en
        sus padres), descartando *args/**kwargs.
        """
        return {
            nombre
            for c in self._get_comportamientos()
            for nombre in self._params_propios(c)
        }

    def _serializar_propios(self) -> dict:
        atributos_comportamientos = self._atributos_de_comportamientos()

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
        atributos_comportamientos = self._atributos_de_comportamientos()

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
        atributos_comportamientos = self._atributos_de_comportamientos()
        for k in list(vars(self).keys()):
            if k not in atributos_comportamientos and not k.startswith("_"):
                setattr(self, k, None)

        # Avisa al mundo para que elimine la referencia
        if self.mundo == None:
            raise TypeError("No se ha inicializado Mundo")
        self.mundo.eliminar_elemento(self)
