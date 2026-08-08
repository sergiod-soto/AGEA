# Core/Entities/Elemento/elemento.py

from __future__ import annotations
from abc import ABC
from typing import TYPE_CHECKING
from numpy import uint64
from Core.Entities.Comportamiento.comportamiento import Comportamiento, NO_SERIALIZAR

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
        id_elemento: uint64,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.capa = capa
        self.tipo = tipo
        self.id_elemento = id_elemento

        self.excluyente_en_celda = False
        self.mundo: Mundo | None = None

    def _get_comportamientos(self) -> list[type]:
        return [
            c
            for c in self.__class__.__mro__
            if issubclass(c, Comportamiento)
            and c is not Comportamiento
            and c._es_comportamiento_real()
            and "__init__" in c.__dict__
        ]

    def _atributos_de_comportamientos(self) -> set[str]:
        """
        Unión de los nombres de atributo que "pertenecen" a cada
        comportamiento presente en este elemento — de su __init__ propio
        o de _campos_internos (ver Comportamiento._campos_serializables).
        """
        return {
            nombre
            for c in self._get_comportamientos()
            for nombre in c._campos_serializables()
        }

    @classmethod
    def _es_comportamiento_real(cls) -> bool:
        return False

    # --- Campos especiales de Elemento (ver README de serialización) ---
    # 'tipo' es la propia clase Python de self: no es JSON-serializable y
    # además es redundante con type(self)/'__clase__'. Se excluye aquí y se
    # restaura en deserializar() a partir de la clase real reconstruida.
    def serialize_tipo(self):
        return NO_SERIALIZAR

    # 'mundo' es la referencia (opcional) al Mundo donde vive el elemento.
    # Serializar el elemento NUNCA debe arrastrar el grafo completo del
    # mundo con él, así que se excluye igual que 'tipo'. Se restaura a
    # None en deserializar(): quien reinserte el elemento en un mundo es
    # responsable de volver a asignarlo.
    def serialize_mundo(self):
        return NO_SERIALIZAR

    def _serializar_propios(self) -> dict:
        atributos_comportamientos = self._atributos_de_comportamientos()

        resultado = {}
        for k, v in vars(self).items():
            if k.startswith("_") or k in atributos_comportamientos:
                continue
            serializador = getattr(self, f"serialize_{k}", None)
            valor = serializador() if serializador else v
            if valor is NO_SERIALIZAR:
                continue
            resultado[k] = valor
        return resultado

    def serializar(self, cls: type | None = None, *, modo: str) -> dict:
        """
        (Por serializar() desde Comportamiento)

        cls : None cuando se serializa el ELEMENTO ENTERO (uso normal:
              _id_a_slot_bytes, save_snapshot, crear_elemento...). Si se
              pasa una clase de comportamiento, es porque quien llama es
              Comportamiento.get_comportamiento() -- que siempre invoca
              self.serializar(cls, modo=modo) -- y en ese caso hay que
              delegar en Comportamiento.serializar para devolver solo
              los campos de ESE comportamiento, no el elemento completo.
              (FIX: antes Elemento.serializar no aceptaba 'cls', así que
              esa llamada rompía con TypeError para cualquier Elemento
              real -- ver Tests/Core/Entities/Elementos/test_elemento.py
              ::test_get_comportamiento_sobre_elemento_real)

        modo distingue PARA QUÉ se serializa, porque un campo pesado (como
        'sonidos' en Sonoro) puede necesitar una representación distinta
        según el consumidor:
        - "guardado"        : snapshots a disco (save_snapshot).
        - "transporte"      : entre sectores / Logica_Mundo vía gRPC
                                (_id_a_slot_bytes). Hoy idéntico a "guardado".
        - "representacion"  : lo que ve Unity cada tick
                                (consultar_representacion) -- lo más ligero
                                posible. Hoy idéntico a los otros dos: sin
                                hooks serialize_X_representacion todavía,
                                pero la distinción existe con vistas a
                                futuro (comentario del usuario, ver
                                sesión de tests).
        """
        if cls is not None:
            return Comportamiento.serializar(self, cls, modo=modo)

        return {
            "__clase__": type(self).__name__,
            **self._serializar_propios(),
            "comportamientos": {
                c.__name__: c.serializar(self, c, modo=modo)
                for c in self._get_comportamientos()
            },
        }

    def deserializar(self, data: dict, mundo: Mundo | None):
        # Deserializa atributos propios del elemento
        atributos_comportamientos = self._atributos_de_comportamientos()

        for k, v in data.items():
            if k in ("__clase__", "comportamientos") or k in atributos_comportamientos:
                continue
            deserializador = getattr(self, f"deserialize_{k}", None)
            if deserializador:
                deserializador(v)
            else:
                setattr(self, k, v)

        # Restaura los campos excluidos de la serialización (ver
        # serialize_tipo/serialize_mundo más arriba). No vienen en 'data':
        # hay que reponerlos explícitamente o el objeto reconstruido se
        # quedaría sin estos atributos (AttributeError al primer uso).
        self.tipo = type(self)
        self.mundo = mundo

        # Delega a cada comportamiento su deserialización
        for c in self._get_comportamientos():
            if c.__name__ in data["comportamientos"]:
                c.deserializar(self, data["comportamientos"][c.__name__])

    def eliminar(self):
        """
        Limpia el estado del elemento antes de descartarlo y avisa al mundo
        para que quite la referencia.

        No se usa Comportamiento.quitar() aquí (opción B, ver discusión):
        quitar() reescribe __class__ para mantener consistente la identidad
        de un objeto que sigue vivo -- trabajo desperdiciado para un objeto
        que va a desaparecer del todo, y que además revienta por cascada
        cuando un comportamiento (p.ej. Fisico) solo está presente en el
        MRO a través de otro (Peso) que se quita antes en el mismo bucle.
        En su lugar, se ponen a None TODOS los atributos propios por igual
        (los del elemento y los de sus comportamientos), sin tocar __class__.
        """
        mundo = self.mundo
        if mundo is None:
            raise TypeError("No se ha inicializado Mundo")

        for k in list(vars(self).keys()):
            if not k.startswith("_"):
                setattr(self, k, None)

        mundo.eliminar_elemento(self)

    @classmethod
    def obtener_requisitos(cls) -> tuple[dict[str, type], set[str]]:
        """
        Retorna:
            (
                {
                    "nombre_atributo": tipo,
                    ...
                },
                {
                    "metodo1",
                    "metodo2",
                    ...
                }
            )
        """

        requiere = set()
        abstractos = set()

        # Desde la clase más base hasta la más derivada.
        # Así las clases hijas pueden sobrescribir requisitos.
        for base in reversed(cls.__mro__):

            requiere.update(getattr(base, "REQUIERE", set()))
            abstractos.update(getattr(base, "ABSTRACTOS", set()))

        return requiere, abstractos
