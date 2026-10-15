# Core/Entities/Elementos/elemento.py

from __future__ import annotations
from abc import ABC
from typing import TYPE_CHECKING
import weakref
from Core.Entities.Comportamiento.comportamiento import Comportamiento

if TYPE_CHECKING:
    from Core.Entities.Mundo.mundo import Mundo

_CAMPOS_PROHIBIDOS_PATCH = frozenset(
    {"id_elemento", "mundo", "tipo", "capa", "casilla"}
)


class Elemento(ABC, Comportamiento):
    """
    Clase base de las cosas que son un elemento, ya sea simple, complejo o abstracto.

    Los elementos existen en el mundo, pueden o no moverse a cambio de energia y
    pueden interactuar entre ellos en funcion de su presencia en las proximidades
    """

    class Flags:
        """
        Registro de los nombres de flag reconocidos por el sistema.
        Cada nombre es un atributo de CLASE que un tipo hoja puede fijar
        a True; el propio nombre es el atributo que se busca con getattr.
        """

        # Marca elementos cuya resistencia_viento no cambia dentro de
        # un tick normal (solo por transformación discreta, igual que Suelo)
        RESISTENCIA_VIENTO_CACHEABLE = "resistencia_viento_cacheable"

    # Flags que esta categoría "contiene". Vacío en la base.
    FLAGS_DISPONIBLES: frozenset[str] = frozenset()

    _TICKS_COMPORTAMIENTO: "weakref.WeakKeyDictionary[type, tuple]" = (
        weakref.WeakKeyDictionary()
    )
    _REQUISITOS_SERIALIZACION: "weakref.WeakKeyDictionary[type, tuple]" = (
        weakref.WeakKeyDictionary()
    )

    @classmethod
    def tiene_flag(cls, nombre: str) -> bool:
        """
        True solo si 'nombre' está en FLAGS_DISPONIBLES (o heredado) Y el
        tipo concreto la fija a True. Preguntar por una flag no contenida
        devuelve False, nunca lanza error.
        """
        if nombre not in cls.FLAGS_DISPONIBLES:
            return False
        return bool(getattr(cls, nombre, False))

    def __init__(
        self,
        tipo: type,
        capa: int,
        id_elemento: int,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.capa = capa
        self.tipo = tipo
        self.id_elemento = id_elemento

        self.excluyente_en_celda = False
        self.mundo: Mundo | None = None

    @classmethod
    def _get_comportamientos(cls) -> list[type]:
        return [
            c
            for c in cls.__mro__
            if issubclass(c, Comportamiento)
            and c is not Comportamiento
            and c._es_comportamiento_real()
            and "__init__" in c.__dict__
        ]

    @classmethod
    def _es_comportamiento_real(cls) -> bool:
        return False

    # ------------------------------------------------------------------
    #  serializar / representar / deserializar
    # ------------------------------------------------------------------
    # Elemento va ANTES que los comportamientos en el MRO, así que su
    # super() recorre primero toda la cadena de comportamientos y vuelve
    # aquí con "comportamientos" ya relleno; Elemento solo añade lo suyo.
    #
    # NO se serializan 'tipo' (es type(self), redundante con '__clase__')
    # ni 'mundo' (arrastraría el grafo entero): se restauran en
    # deserializar().
    @classmethod
    def _requisitos_serializacion(cls) -> tuple:
        """((comportamiento, frozenset(campos)), ...) de cada comportamiento real
        del MRO. Se calcula una vez por clase."""
        req = Elemento._REQUISITOS_SERIALIZACION.get(cls)
        if req is None:
            req = tuple(
                (c, frozenset(c._campos_serializables()))
                for c in cls._get_comportamientos()
            )
            Elemento._REQUISITOS_SERIALIZACION[cls] = req
        return req

    def serializar_id_elemento(self):
        return int(self.id_elemento)

    def serializar(self) -> dict:
        datos = super().serializar()

        # GUARDA: reconstruir_elemento() QUITA los comportamientos cuya sección
        # no aparece en el snapshot, y el Sector reconstruye con __new__ (sin
        # __init__): un campo que no viaja en la sección no existe allí y falla
        # lejos, en un tick posterior. Por eso cada comportamiento debe:
        #  - sin campos propios (categorías: Fisico, Informativo...) -> {}
        #  - con campos -> una sección que contenga TODOS (con el mismo nombre
        #    que su atributo). Se reúnen todos los fallos en un solo error.
        secciones = datos["comportamientos"]
        problemas = []
        for c, campos in self._requisitos_serializacion():
            seccion = secciones.get(c.__name__)
            if seccion is None:
                if campos:
                    problemas.append(
                        f"{c.__name__}: no escribe sección (campos {sorted(campos)})"
                    )
                else:
                    secciones[c.__name__] = {}
                continue
            faltan = campos - seccion.keys()
            if faltan:
                problemas.append(f"{c.__name__}: su sección no guarda {sorted(faltan)}")
        if problemas:
            raise NotImplementedError(
                f"{type(self).__name__}.serializar(): " + "; ".join(problemas) + "."
            )

        return {
            "__clase__": type(self).__name__,  # lo lee reconstruir_elemento()
            "id_elemento": self.serializar_id_elemento(),
            "capa": self.capa,
            **datos,
        }

    def representar(self, incluir: list[str] | None = None) -> dict:
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["elemento"].update(
                {
                    "__clase__": type(self).__name__,
                    "entidad": "elemento",
                    "capa": self.capa,
                    "id_elemento": self.serializar_id_elemento(),
                }
            )
        return datos

    def deserializar(self, data: dict, mundo: Mundo | None = None) -> None:
        super().deserializar(data, mundo)
        self.capa = data["capa"]
        self.id_elemento = data["id_elemento"]
        # Campos excluidos de la serialización: se reponen aquí o el objeto
        # reconstruido no los tendría (AttributeError al primer uso).
        self.tipo = type(self)
        self.mundo = mundo
        # 'excluyente_en_celda' no se serializa: se repone con el valor que
        # le da Elemento.__init__. Si algún tipo concreto lo pone a True en
        # su __init__, deberá volver a ponerlo en su propio deserializar().
        self.excluyente_en_celda = False

    @classmethod
    def obtener_requisitos(cls) -> tuple[dict[str, type], set[str]]:
        """
        Retorna ({"nombre_atributo": tipo, ...}, {"metodo1", ...}),
        recorriendo el MRO de la base a la derivada para que las hijas
        puedan sobrescribir requisitos.
        """
        requiere = set()
        abstractos = set()

        for base in reversed(cls.__mro__):
            requiere.update(getattr(base, "REQUIERE", set()))
            abstractos.update(getattr(base, "ABSTRACTOS", set()))

        return requiere, abstractos

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        """
        Atributos necesarios para construir esta clase desde fuera
        (consola). Cada tipo concreto creable DEBE sobrescribirlo; se
        deja sin implementar a propósito para que falle alto.
        """
        raise NotImplementedError(
            f"{cls.__name__} no implementa campos_para_creacion(); no se puede "
            "crear este tipo de elemento desde la consola todavía."
        )

    def aplicar_patch(self, patch: dict) -> None:
        prohibidos = _CAMPOS_PROHIBIDOS_PATCH & patch.keys()
        if prohibidos:
            raise ValueError(f"Campos no modificables por patch: {sorted(prohibidos)}")

        # Validar TODO antes de aplicar nada (un patch no queda a medias).
        for atributo in patch:
            if not hasattr(self, f"deserializar_{atributo}") and not hasattr(
                self, atributo
            ):
                raise AttributeError(
                    f"{type(self).__name__} no tiene el campo '{atributo}'"
                )
        for atributo, valor in patch.items():
            deserializador = getattr(self, f"deserializar_{atributo}", None)
            if deserializador:
                deserializador(valor)
            else:
                setattr(self, atributo, valor)

    @classmethod
    def _comportamiento_de_campo(cls, nombre: str):
        """
        Qué Comportamiento del MRO declara 'nombre' entre sus
        _campos_serializables() (lo usa la consola para la ayuda).
        """
        for c in cls.__mro__:
            if (
                issubclass(c, Comportamiento)
                and c is not Comportamiento
                and c._es_comportamiento_real()
                and "__init__" in c.__dict__
                and nombre in c._campos_serializables()
            ):
                return c
        return None

    @classmethod
    def ayuda_creacion(cls) -> str:
        raise NotImplementedError(
            f"{cls.__name__} no implementa ayuda_creacion(); no hay texto "
            "de ayuda definido para este tipo de elemento todavía."
        )

    @classmethod
    def _ticks_comportamiento(cls) -> tuple:
        """tick_comportamiento propios de cada comportamiento real del MRO, en
        orden de MRO (= orden de declarar_comportamientos). Se calcula una vez
        por clase: recorrer el MRO en cada tick triplicaba el coste."""
        ticks = Elemento._TICKS_COMPORTAMIENTO.get(cls)
        if ticks is None:
            ticks = tuple(
                c.__dict__["tick_comportamiento"]
                for c in cls.__mro__
                if issubclass(c, Comportamiento)
                and c._es_comportamiento_real()
                and "tick_comportamiento" in c.__dict__
            )
            Elemento._TICKS_COMPORTAMIENTO[cls] = ticks
        return ticks

    def tick_elemento(self, ctx) -> None:
        """
        Lógica propia del tipo en cada tick. Cada tipo concreto DEBE
        sobrescribirlo (aunque sea con `pass`): se deja sin implementar a
        propósito para que un tipo sin tick falle alto.
        """
        raise NotImplementedError(
            f"{type(self).__name__} no implementa tick_elemento(ctx); aunque no "
            "haga nada, debe declararlo explícitamente."
        )

    def tick(self, ctx) -> None:
        """
        Tick completo del elemento. NO se sobrescribe: primero la lógica del
        propio elemento (tick_elemento) y después la de cada comportamiento
        (tick_comportamiento).
        """
        self.tick_elemento(ctx)
        for tick_comportamiento in self._ticks_comportamiento():
            tick_comportamiento(self, ctx)
