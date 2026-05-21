from abc import abstractmethod
from dataclasses import dataclass
import inspect


@dataclass(kw_only=True)
class Comportamiento:
    """
    Metodos abstractos:

    - serializar()
    - deserializar()

    Lista de argumentos de cada comportamiento:

    - Empujable:
        - coste_empujar: float
        - empujable: bool

    - Enterrable: -
    - Flotable:
        - flotable: bool
    - Humedo:
        - humedad_max: float
        - humedad_actual: float
    - Inflamable:
        - temperatura_ignicion: float
        - inflamable: bool
        - ardiendo: bool
    - Peso:
        - peso: float
    - Volumen:
        - volumen: float
    - Color:
        - rgb_color: tuple[int, int, int]
    - Luminoso:
        - distancia_luz: float
        - area_luz: int = 360
    - Rastreable:
        - condiciones_rastro: list[tuple[list[Condicion], float]]
    - Sonoro: -
    - Agarrable:
        - agarrado_por: Elemento
    - Consumible: -
    - Contenedor:
        - capacidad: float
        - contenido: list[Elemento]
    - Crafteable:
        - receta: tuple[str, list[Elemento]]
    - Destruible:
        - durabilidad_max: float
        - durabilidad_actual: float
    - Equipable:
        - provoca_equiparlo: dict[Elemento, Accion]
        - equipado_por: Elemento
    - Golpeable: -
    - Ingrediente:
        - recetas: dict[str, Crafteable]
    - Interactuable: -
    - Plantable:
        - plantado: bool
        - plantable: bool
    - Recolectable:
        - contenido: dict[str, tuple[Elemento, float]]
    - Combinable:
        - elemento_combinable: Elemento
        - cantidad_max_combinable: float
    - Divisible:
        - cantidad_minima_divisible:float
    - Erosionable:
        - condiciones_erosion: list[tuple[list[Condicion], float]]
        - durabilidad_max_erosion: float
        - durabilidad_actual_erosion: float
    - Gaseoso: -
    - Liquido: -
    - Solido: -
    - Tangible: -
    - Transformable:
        - dict: dict[Condicion, Elemento]
    - Transparente: -
    - Comestible: -
    - Hidratante:
        - valor_hidratacion: float
    - Medicinal:
        - valor_medicinal: float
    - Nutritivo:
        - valor_nutritivo: float
    - Regenerable:
        - tasas_regeneracion: list[tuple[Stat, float]]
    - Toxico:
        - valor_toxico: float
    - Intercambiable: -
    - Caduco:
        - duracion_max_caduco: int
        - duracion_restante_caduco: int
    - Estacional:
        - acciones_por_estacion: dict[Estacion, list[Accion]]
    - Latente:
        - condiciones: list[Condicion]
        - accion_latente: Accion
    - Perecedero:.
        - tiempo_maximo_perecedero: float
        - condiciones_perecedero: list[tuple[list[Condicion], float]]
        - tiempo_actual_perecedero: float
    - Temporal: -

    ________________________________________________________

    STATS:

    - Ataque: -
    - Defensa: -
    - Deteccion: -
    - Edad_Adulta: -
    - Edad: -
    - Energia: -
    - Regulacion_Temperatura: -
    - Salud: -
    - Sigilo: -
    - Temperatura: -
    - Velocidad: -

    - Agresividad: -
    - Armadura: -
    - Grasa: -
    - Longevidad: -
    - Movilidad: -
    - Percepcion: -
    - Tamanho: -
    - Temperatura_Optima: -

    - Apellidos: -
    - ID: -
    - Posicion: -
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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

    @staticmethod
    def anhadir(obj, comportamiento: type, **kwargs):
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
        if not isinstance(obj, comportamiento):
            raise TypeError(
                f"{obj.__class__.__name__} no tiene {comportamiento.__name__}"
            )

        # Atributos de todos los comportamientos que se mantienen
        campos_restantes = {
            nombre
            for cls in obj.__class__.__mro__
            if cls is not comportamiento and cls is not obj.__class__
            for nombre in Comportamiento._params_propios(cls)
        }

        for nombre in Comportamiento._params_propios(comportamiento):
            if nombre not in campos_restantes and hasattr(obj, nombre):
                delattr(obj, nombre)

        bases_sin = tuple(b for b in obj.__class__.__bases__ if b is not comportamiento)
        obj.__class__ = type(obj.__class__.__name__, bases_sin, {})

    def comportamientos(self) -> list["Comportamiento"]:
        """Retorna todos los comportamientos de la entidad"""

        return [
            c
            for c in type(self).__mro__
            if issubclass(c, Comportamiento) and c is not Comportamiento
        ]

    def comportamientos_de(self, categoria) -> list["Comportamiento"]:
        """Retorna que comportamientos se han heredado de cierta categoria"""

        return [
            c
            for c in type(self).__mro__
            if issubclass(c, categoria) and c is not categoria
        ]

    def categorias(self) -> list["Comportamiento"]:
        """
        retorna las categorias que contienen comportamientos presentes en la entidad
        """

        categorias = Comportamiento.__subclasses__()
        return [c for c in type(self).__mro__ if c in categorias]

    def tiene_comportamiento(self, comportamiento) -> bool:
        """Pregunta si el elemento tiene X comportamiento"""
        return isinstance(self, comportamiento)

    # --- Representación ---
    def __repr__(self):
        nombres = [c.__name__ for c in self.comportamientos()]
        return f"{type(self).__name__}({', '.join(nombres)})"

    # --- Serialización  ---
    def a_dict(self) -> dict:
        """Exporta el estado del objeto como diccionario"""
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def desde_dict(cls, datos: dict):
        obj = cls.__new__(cls)
        obj.__dict__.update(datos)
        return obj

    def declarar_comportamientos(*clases):
        """Permite definir de forma externa los comportamientos del Elemento, clarificando sus herencias"""
        return type("Comportamientos", clases, {})

    def serializar(self):
        """
        Serializa automaticamente los atributos de clase en un dict.

        No necesariamente puede serializar todos los atributos, en algunos
        casos es necesario trabajo extra personalizado. En ese caso,
        hay que definir el metodo serializar() en la propia clase, llamando
        primero a super().serializar() y añadiendole luego las entradas necesarias.
        """

        return dict(vars(self))

    def deserializar(self, data: dict):
        """
        Da valores a los atributos de la clase automaticamente a partir de un dict.

        Algunos valores no son deserializables automaticamente y deberan hacerse a mano.
        En ese caso, la clase debe implementar este metodo, deserializando manualmente la variable
        problematica en, por ejemplo, data y posteriormente llamando a super().deserializar(data)
        """

        for key, value in data.items():
            setattr(self, key, value)
