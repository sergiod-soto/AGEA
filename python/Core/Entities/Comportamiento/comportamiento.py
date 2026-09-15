# Core/Entities/Comportamiento/comportamiento.py

from dataclasses import dataclass
import inspect

from Core.Entities.entity import Modos


class _NoSerializar:
    """
    Sentinel que un serialize_X() puede devolver para decir "este campo no
    debe aparecer en el dict serializado". Es el mismo mecanismo de hooks
    (serialize_X/deserialize_X) el que decide EXCLUIR un campo, no una
    lista aparte de excepciones — así solo hay una vía para tratar campos
    especiales, tanto a nivel de Comportamiento como de Elemento.
    """

    pass


NO_SERIALIZAR = _NoSerializar()


@dataclass(kw_only=True)
class Comportamiento:

    def __init__(self): ...

    @staticmethod
    def _params_propios(cls) -> dict:
        """Parámetros definidos en el __init__ de esta clase concreta (no heredados)."""
        if "__init__" not in cls.__dict__:
            return {}
        sig = inspect.signature(cls.__init__)
        return {
            nombre: param
            for nombre, param in sig.parameters.items()
            if nombre != "self"
            and param.kind
            not in (
                inspect.Parameter.VAR_POSITIONAL,  # *args
                inspect.Parameter.VAR_KEYWORD,  # **kwargs
            )
        }

    @classmethod
    def _campos_internos(cls) -> set[str]:
        """
        Nombres de atributos propios de esta clase que deben serializarse
        aunque NO sean parámetros de su __init__ — p.ej. estado interno
        (privado, con guion bajo) que se inicializa en el cuerpo del
        constructor en vez de recibirse como argumento (self._enterrado,
        self._comportamiento_activo...).

        Por defecto vacío: la mayoría de comportamientos no lo necesitan,
        porque todos sus datos ya son parámetros de __init__ (p.ej. Peso).
        Una subclase la sobreescribe solo cuando tiene ese caso.
        """
        return set()

    @classmethod
    def _es_comportamiento_real(cls) -> bool:
        """
        True si esta clase debe tratarse como un comportamiento con
        identidad propia (sus parámetros cuentan para decidir qué se
        conserva/elimina en quitar()). Por defecto True para cualquier
        subclase de Comportamiento; Elemento la sobreescribe a False para
        excluirse a sí mismo y a toda su cadena (Elemento_Simple,
        Elemento_Test...) sin que Comportamiento tenga que conocer a
        Elemento (evita el import circular).
        """
        return True

    @classmethod
    def _campos_serializables(cls) -> set[str]:
        """
        Unión de ambas fuentes: lo que se recibe por __init__ + lo que se
        declara explícitamente como interno. Es la fuente única de verdad
        de "qué atributos pertenecen a este comportamiento", tanto para
        Comportamiento.serializar() como para que Elemento sepa qué NO debe
        tratar como atributo propio suyo.
        """
        return set(Comportamiento._params_propios(cls).keys()) | cls._campos_internos()

    @staticmethod
    def _sin_comportamiento(clase: type, comportamiento: type):
        """
        Devuelve una versión de `clase` sin `comportamiento`, reconstruyendo
        recursivamente cualquier base compuesta (como las que genera
        declarar_comportamientos, o las que anhadir() va encadenando) que lo
        contenga. Si `clase` no tiene ninguna relación con `comportamiento`
        (no está en su MRO), se devuelve TAL CUAL, sin recrear nada — así
        Elemento_Simple, por ejemplo, nunca se toca.
        """
        if clase is comportamiento:
            return None  # esta rama desaparece por completo
        if not issubclass(clase, comportamiento):
            return clase  # no relacionado, se conserva intacto

        nuevas_bases = tuple(
            nueva
            for nueva in (
                Comportamiento._sin_comportamiento(base, comportamiento)
                for base in clase.__bases__
            )
            if nueva is not None
        )
        if not nuevas_bases:
            nuevas_bases = (object,)
        return type(clase.__name__, nuevas_bases, {})

    @staticmethod
    def anhadir(obj, comportamiento: type, **kwargs):
        """
        añadir comportamiento a un Elemento
        """

        if isinstance(obj, comportamiento):
            raise TypeError(
                f"{obj.__class__.__name__} ya tiene {comportamiento.__name__}"
            )
        nueva_clase = type(obj.__class__.__name__, (obj.__class__, comportamiento), {})
        obj.__class__ = nueva_clase

        # atributos del __init__
        for nombre, param in Comportamiento._params_propios(comportamiento).items():
            if hasattr(obj, nombre):
                continue
            if nombre in kwargs:
                valor = kwargs[nombre]
            elif param.default is not inspect.Parameter.empty:
                valor = param.default
            else:
                raise ValueError(
                    f"{comportamiento.__name__} requiere el atributo '{nombre}'"
                )
            setattr(obj, nombre, valor)

        # metodos abstractos
        for nombre in getattr(comportamiento, "__abstractmethods__", set()):
            if nombre in kwargs:
                setattr(obj, nombre, kwargs[nombre].__get__(obj, obj.__class__))
            else:
                raise ValueError(
                    f"{comportamiento.__name__} requiere el método '{nombre}'"
                )

    @staticmethod
    def quitar(obj, comportamiento: type):
        """
        Eliminar Comportamiento de un Elemento — funciona tanto si
        `comportamiento` es base directa de obj.__class__ (caso típico de
        anhadir()) como si quedó anidado dentro de una clase compuesta
        (declarar_comportamientos, o encadenamientos de anhadir()).
        """
        if not isinstance(obj, comportamiento):
            raise TypeError(
                f"{obj.__class__.__name__} no tiene {comportamiento.__name__}"
            )

        presentes = [
            c
            for c in obj.__class__.__mro__
            if issubclass(c, Comportamiento)
            and c is not Comportamiento
            and c._es_comportamiento_real()
            and "__init__" in c.__dict__
        ]

        campos_restantes = {
            nombre
            for c in presentes
            if c is not comportamiento
            for nombre in Comportamiento._params_propios(c)
        }
        for nombre in Comportamiento._params_propios(comportamiento):
            if nombre not in campos_restantes and hasattr(obj, nombre):
                delattr(obj, nombre)

        nuevas_bases = tuple(
            nueva
            for nueva in (
                Comportamiento._sin_comportamiento(base, comportamiento)
                for base in obj.__class__.__bases__
            )
            if nueva is not None
        )
        obj.__class__ = type(obj.__class__.__name__, nuevas_bases, {})

    def comportamientos(self) -> list[type]:
        """
        Retorna todos los comportamientos (CLASES, no instancias) de la
        entidad. Devuelve clases porque, al ser mixins fusionados en el
        MRO, no existe una instancia separada por comportamiento.
        """

        return [
            c
            for c in type(self).__mro__
            if issubclass(c, Comportamiento) and c is not Comportamiento
        ]

    def categorias(self) -> list[type]:
        """
        Retorna las categorías (CLASES) que contienen comportamientos
        presentes en la entidad.
        """

        categorias = Comportamiento.__subclasses__()
        return [c for c in type(self).__mro__ if c in categorias]

    def tiene_comportamiento(self, comportamiento) -> bool:
        """
        Pregunta si el elemento tiene X comportamiento
        """
        return isinstance(self, comportamiento)

    def get_comportamiento(self, nombre: str, *, modo: Modos) -> dict:
        for cls in self.comportamientos():
            if cls.__name__ == nombre:
                return self.serializar(cls, modo=modo)
        raise ValueError(f"{type(self).__name__} no tiene el comportamiento '{nombre}'")

    # --- Representación ---
    def __repr__(self):
        nombres = [c.__name__ for c in self.comportamientos()]
        return f"{type(self).__name__}({', '.join(nombres)})"

    def declarar_comportamientos(*clases):
        """Permite definir de forma externa los comportamientos del Elemento, clarificando sus herencias"""
        return type("Comportamientos", clases, {})

    def serializar(self, cls=None, *, modo: Modos) -> dict:
        """
        modo distingue PARA QUÉ se serializa, porque un campo pesado (como
        'sonidos' en Sonoro) puede necesitar una representación distinta
        según el consumidor:
        - "guardado"        : snapshots a disco (save_snapshot).
        - "transporte"      : entre sectores / Logica_Mundo vía gRPC
                                (_id_a_slot_bytes). Hoy idéntico a "guardado"
                                (ambos necesitan fidelidad total para poder
                                reconstruir el elemento), separado como modo
                                aparte por si algún día divergen (p.ej. el
                                transporte quisiera comprimir algo que el
                                guardado no).
        - "representacion"  : lo que ve Unity cada tick
                                (consultar_representacion) -- lo más ligero
                                posible.
        """

        cls = cls or type(self)
        atributos = cls._campos_serializables()
        resultado = {}
        for nombre in atributos:
            especifico = getattr(self, f"serialize_{nombre}_{modo.value}", None)
            generico = getattr(self, f"serialize_{nombre}", None)
            serializador = especifico or generico
            if serializador:
                valor = serializador()
            elif hasattr(self, nombre):
                valor = getattr(self, nombre)
            else:
                continue
            if valor is NO_SERIALIZAR:
                continue
            resultado[nombre] = valor

        return resultado

    def deserializar(self, data: dict):
        """
        Da valores a los atributos de la clase a partir de un dict.

        Para cada clave, si existe un método deserialize_<clave> en la
        instancia, se le delega la reconstrucción del valor (p.ej. deshacer
        una transformación de formato hecha en serialize_<clave>). Si no
        existe, se hace un setattr directo del valor tal cual llega.
        """
        for key, value in data.items():
            deserializador = getattr(self, f"deserialize_{key}", None)
            if deserializador:
                deserializador(value)
            else:
                setattr(self, key, value)

    @classmethod
    def ayuda_creacion(cls) -> str:
        """
        Texto explicativo que la consola muestra con 'ayuda <Comportamiento>'
        -- qué es este comportamiento y cómo afecta al elemento que lo
        tiene. Cada comportamiento concreto DEBE sobrescribirlo -- se
        deja sin implementar a propósito, igual que campos_para_creacion(),
        para que un comportamiento nuevo sin documentar falle alto en
        vez de mostrar un hueco vacío en silencio.
        """
        raise NotImplementedError(
            f"{cls.__name__} no implementa ayuda_creacion(); no hay texto "
            "de ayuda definido para este comportamiento todavía."
        )

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        raise NotImplementedError(
            f"{cls.__name__} no implementa campos_para_creacion(). No puede ser creado por consola."
        )


