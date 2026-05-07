from dataclasses import dataclass
import inspect

from Core.Entities.Comportamiento.Energetico.combustible import Combustible
from Core.Entities.Comportamiento.Energetico.termico import Termico
from Core.Entities.Comportamiento.Fisico.empujable import Empujable
from Core.Entities.Comportamiento.Fisico.enterrable import Enterrable
from Core.Entities.Comportamiento.Fisico.flotable import Flotable
from Core.Entities.Comportamiento.Fisico.humedo import Humedo
from Core.Entities.Comportamiento.Fisico.inflamable import Inflamable
from Core.Entities.Comportamiento.Fisico.peso import Peso
from Core.Entities.Comportamiento.Fisico.volumen import Volumen
from Core.Entities.Comportamiento.Informativo.color import Color
from Core.Entities.Comportamiento.Informativo.luminoso import Luminoso
from Core.Entities.Comportamiento.Informativo.rastreable import Rastreable
from Core.Entities.Comportamiento.Informativo.sonoro import Sonoro
from Core.Entities.Comportamiento.Interaccion.agarrable import Agarrable
from Core.Entities.Comportamiento.Interaccion.consumible import Consumible
from Core.Entities.Comportamiento.Interaccion.contenedor import Contenedor
from Core.Entities.Comportamiento.Interaccion.crafteable import Crafteable
from Core.Entities.Comportamiento.Interaccion.destruible import Destruible
from Core.Entities.Comportamiento.Interaccion.equipable import Equipable
from Core.Entities.Comportamiento.Interaccion.golpeable import Golpeable
from Core.Entities.Comportamiento.Interaccion.ingrediente import Ingrediente
from Core.Entities.Comportamiento.Interaccion.interactuable import Interactuable
from Core.Entities.Comportamiento.Interaccion.plantable import Plantable
from Core.Entities.Comportamiento.Interaccion.recolectable import Recolectable
from Core.Entities.Comportamiento.Material.combinable import Combinable
from Core.Entities.Comportamiento.Material.divisible import Divisible
from Core.Entities.Comportamiento.Material.erosionable import Erosionable
from Core.Entities.Comportamiento.Material.gaseoso import Gaseoso
from Core.Entities.Comportamiento.Material.liquido import Liquido
from Core.Entities.Comportamiento.Material.solido import Solido
from Core.Entities.Comportamiento.Material.tangible import Tangible
from Core.Entities.Comportamiento.Material.transformable import Transformable
from Core.Entities.Comportamiento.Material.transparente import Transparente
from Core.Entities.Comportamiento.Salud.comestible import Comestible
from Core.Entities.Comportamiento.Salud.hidratante import Hidratante
from Core.Entities.Comportamiento.Salud.medicinal import Medicinal
from Core.Entities.Comportamiento.Salud.nutritivo import Nutritivo
from Core.Entities.Comportamiento.Salud.regenerable import Regenerable
from Core.Entities.Comportamiento.Salud.toxico import Toxico
from Core.Entities.Comportamiento.Social.intercambiable import Intercambiable
from Core.Entities.Comportamiento.Temporal.caduco import Caduco
from Core.Entities.Comportamiento.Temporal.estacional import Estacional
from Core.Entities.Comportamiento.Temporal.latente import Latente
from Core.Entities.Comportamiento.Temporal.perecedero import Perecedero
from Core.Entities.Comportamiento.Temporal.temporal import Temporal


@dataclass(kw_only=True)
class Comportamiento:
    """
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
    def añadir(obj, comportamiento: type, **kwargs):
        if isinstance(obj, comportamiento):
            raise TypeError(
                f"{obj.__class__.__name__} ya tiene {comportamiento.__name__}"
            )

        nueva_clase = type(obj.__class__.__name__, (obj.__class__, comportamiento), {})
        obj.__class__ = nueva_clase

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
        retorna las categorias con comportamientos presentes en la entidad
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


def get_parametros(comportamientos: list[Comportamiento]):
    partes = []
    for c in comportamientos:
        if c is Combustible:
            partes.append(
                "energia_maxima: float, ratio_emision: float, energia_actual: float = None, ratio_recarga: float = 0.0, "
            )
        elif c is Termico:
            partes.append(
                "temperatura_propia: float, tasa_transferencia: float, radio_termico: float, "
            )
        #
        elif c is Empujable:
            partes.append("")
        elif c is Enterrable:
            partes.append("coste_empujar= float, ")
        elif c is Flotable:
            partes.append("")
        elif c is Humedo:
            partes.append("humedad_max= float, ")
        elif c is Inflamable:
            partes.append("temperatura_ignicion= float, ")
        elif c is Peso:
            partes.append("peso= float, ")
        elif c is Volumen:
            partes.append("volumen= float, ")
        #
        elif c is Color:
            partes.append("rgb_color= tuple[int, int, int], ")
        elif c is Luminoso:
            partes.append("distancia_luz= float, area_luz= int = 360, ")
        elif c is Rastreable:
            partes.append(
                "condiciones_rastro= list[tuple[list[Condicion], float]] = None, "
            )
        elif c is Sonoro:
            partes.append("")
        #
        elif c is Agarrable:
            partes.append("agarrado_por= Elemento, ")
        elif c is Consumible:
            partes.append("")
        elif c is Contenedor:
            partes.append("capacidad= float, contenido= list[Elemento] = None, ")
        elif c is Crafteable:
            partes.append("receta_para= tuple[str, list[Elemento]], ")
        elif c is Destruible:
            partes.append("durabilidad_max= float, durabilidad_actual= float = None, ")
        elif c is Equipable:
            partes.append(
                "provoca_equiparlo= dict[Elemento, Accion] = None, equipado_por= Elemento = None, "
            )
        elif c is Golpeable:
            partes.append("")
        elif c is Ingrediente:
            partes.append("recetas_de= dict[str, Crafteable], ")
        elif c is Interactuable:
            partes.append("")
        elif c is Plantable:
            partes.append("plantado= bool = False, ")
        elif c is Recolectable:
            partes.append("contenido= dict[str, tuple[Elemento, float]] = None, ")
        #
        elif c is Combinable:
            partes.append(
                "elemento_combinable= Elemento, cantidad_max_combinable= float = None, "
            )
        elif c is Divisible:
            partes.append("cantidad_minima_divisible= float, ")
        elif c is Erosionable:
            partes.append(
                "condiciones_erosion= list[tuple[list[Condicion], float]], durabilidad_max_erosion= float, durabilidad_actual_erosion= float = None, "
            )
        elif c is Gaseoso:
            partes.append("")
        elif c is Liquido:
            partes.append("")
        elif c is Solido:
            partes.append("")
        elif c is Tangible:
            partes.append("")
        elif c is Transformable:
            partes.append("dict_transformable= dict[Condicion, Elemento], ")
        elif c is Transparente:
            partes.append("")
        #
        elif c is Comestible:
            partes.append("")
        elif c is Hidratante:
            partes.append("valor_hidratacion= float, ")
        elif c is Medicinal:
            partes.append("valor_medicinal= float, ")
        elif c is Nutritivo:
            partes.append("valor_nutritivo= float, ")
        elif c is Regenerable:
            partes.append("tasas_regeneracion= list[tuple[Stat, float]], ")
        elif c is Toxico:
            partes.append("valor_toxico= float, ")
        #
        elif c is Intercambiable:
            partes.append("")
        #
        elif c is Caduco:
            partes.append(
                "duracion_max_caduco= int, duracion_restante_caduco= int = None, "
            )
        elif c is Estacional:
            partes.append("acciones_por_estacion= dict[Estacion, list[Accion]], ")
        elif c is Latente:
            partes.append("condiciones= list[Condicion], accion_latente= Accion, ")
        elif c is Perecedero:
            partes.append(
                "tiempo_maximo_perecedero= float, condiciones_perecedero= list[tuple[list[Condicion], float]], tiempo_actual_perecedero= float = None, "
            )
        elif c is Temporal:
            partes.append("")
        #

    return "".join(partes)

