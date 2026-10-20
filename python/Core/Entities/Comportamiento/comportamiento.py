# Core/Entities/Comportamiento/comportamiento.py

import inspect


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
        Atributos propios de esta clase que no son parámetros de su
        __init__ (estado interno inicializado en el cuerpo del
        constructor). Por defecto vacío; una subclase lo sobrescribe
        solo si lo necesita.
        """
        return set()

    @classmethod
    def _es_comportamiento_real(cls) -> bool:
        """
        True si esta clase es un comportamiento con identidad propia.
        Elemento lo sobrescribe a False para excluirse a sí mismo y a su
        cadena (Elemento_Simple, Piedra...) sin que Comportamiento tenga
        que conocer a Elemento (evita el import circular).
        """
        return True

    @classmethod
    def _campos_serializables(cls) -> set[str]:
        """
        Nombres de atributo que "pertenecen" a este comportamiento: los
        del __init__ + los internos. Ya NO se usa para serializar (ahora
        es manual); se usa en la guarda de Elemento.serializar (detectar
        comportamientos con datos que no escribieron su sección) y en
        Elemento._comportamiento_de_campo (ayuda de la consola).
        """
        return set(Comportamiento._params_propios(cls).keys()) | cls._campos_internos()

    @staticmethod
    def _sin_comportamiento(clase: type, comportamiento: type):
        """
        Devuelve una versión de `clase` sin `comportamiento`, reconstruyendo
        recursivamente cualquier base compuesta que lo contenga. Si `clase`
        no tiene relación con `comportamiento`, se devuelve TAL CUAL.
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
        `comportamiento` es base directa de obj.__class__ como si quedó
        anidado dentro de una clase compuesta.
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
        Todos los comportamientos (CLASES, no instancias) de la entidad.
        """
        return [
            c
            for c in type(self).__mro__
            if issubclass(c, Comportamiento) and c is not Comportamiento
        ]

    def categorias(self) -> list[type]:
        """
        Las categorías (CLASES) que contienen comportamientos presentes.
        """
        categorias = Comportamiento.__subclasses__()
        return [c for c in type(self).__mro__ if c in categorias]

    def tiene_comportamiento(self, comportamiento) -> bool:
        return isinstance(self, comportamiento)

    def get_comportamiento(self, nombre: str) -> dict:
        """
        Sección serializada de UN comportamiento. Con la cadena super()
        no se puede serializar "solo uno": se serializa todo y se extrae
        su sección (coste aceptado: es una consulta puntual, no el tick).
        """
        for cls in self.comportamientos():
            if cls.__name__ == nombre:
                return self.serializar()["comportamientos"].get(nombre, {})
        raise ValueError(f"{type(self).__name__} no tiene el comportamiento '{nombre}'")

    # --- Representación ---
    def __repr__(self):
        nombres = [c.__name__ for c in self.comportamientos()]
        return f"{type(self).__name__}({', '.join(nombres)})"

    @staticmethod
    def declarar_comportamientos(*clases):
        """Permite definir de forma externa los comportamientos del Elemento, clarificando sus herencias"""
        return type("Comportamiento", clases, {})

    # ------------------------------------------------------------------
    #  serializar / representar / deserializar  (cadena super() cooperativa)
    # ------------------------------------------------------------------
    #
    # PATRÓN: cada clase de la cadena (de Elemento Y de los comportamientos)
    # define estos métodos con la MISMA firma, llama primero a super() y
    # añade solo lo suyo al dict recibido. Comportamiento es el FINAL de la
    # cadena: crea el contenedor vacío.
    #
    # REGLA DE ORO: si una clase define uno de estos métodos y no llama a
    # super(), corta la cadena en silencio. Misma firma en todas:
    #     serializar(self) -> dict
    #     representar(self, incluir=None) -> dict
    #     deserializar(self, data, mundo=None) -> None
    #
    # Formatos (se mantienen los de antes, a propósito):
    #   serializar  -> PLANO: {"__clase__", campos del elemento...,
    #                          "comportamientos": {Nombre: {...}}}
    #   representar -> {"elemento": {...}, "comportamientos": {Nombre: {...}}}

    @staticmethod
    def _incluido(incluir: list[str] | None, clase: type) -> bool:
        """
        Filtro 'incluir' de representar(). None o [] = SIN filtro (se
        incluye todo); si la lista tiene nombres, la clase se incluye solo
        si su nombre está en ella. Así un campo 'repeated' del proto sin
        enviar (que llega como []) significa "todo" sin conversiones.
        Cada clase lo consulta con SU propio __class__ antes de escribir
        su parte.
        """
        return not incluir or clase.__name__ in incluir

    def serializar(self) -> dict:
        """Final de la cadena: contenedor vacío. Siempre COMPLETO (sin
        `incluir`): un snapshot no puede ser parcial."""
        return {"comportamientos": {}}

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Final de la cadena. Devuelve el contenedor con la forma que
        espera Unity; las clases de Elemento rellenan "elemento" y los
        comportamientos rellenan "comportamientos"."""
        return {"elemento": {}, "comportamientos": {}}

    def deserializar(self, data: dict, mundo=None) -> None:
        """Final de la cadena: no hay nada que restaurar aquí. Cada clase
        lee su parte de `data` y llama antes a super()."""
        return None

    @classmethod
    def ayuda_creacion(cls) -> str:
        """
        Texto que la consola muestra con 'ayuda <Comportamiento>'. Cada
        comportamiento concreto DEBE sobrescribirlo (falla alto si no).
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
