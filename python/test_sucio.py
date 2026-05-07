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
from Core.Entities.Comportamiento.comportamiento import Comportamiento


def get_parametros(comportamientos: list[Comportamiento]):
    partes = []
    partes_opcionales = []
    partes.append("\n")
    for c in comportamientos:
        if c is Combustible:
            partes.append("energia_maxima: float, ratio_emision: float,   ")
            partes_opcionales.append(
                "energia_actual: float = None, ratio_recarga: float = 0.0,"
            )
        elif c is Termico:
            partes.append(
                "temperatura_propia: float, tasa_transferencia: float, radio_termico: float, "
            )
        #
        elif c is Empujable:
            partes.append("")
        elif c is Enterrable:
            partes.append("coste_empujar: float, ")
        elif c is Flotable:
            partes.append("")
        elif c is Humedo:
            partes.append("humedad_max: float, ")
        elif c is Inflamable:
            partes.append("temperatura_ignicion: float, ")
        elif c is Peso:
            partes.append("peso: float, ")
        elif c is Volumen:
            partes.append("volumen: float, ")
        #
        elif c is Color:
            partes.append("rgb_color: tuple[int, int, int], ")
        elif c is Luminoso:
            partes.append("distancia_luz: float, ")
            partes_opcionales.append("area_luz: int = 360, ")
        elif c is Rastreable:
            partes_opcionales.append(
                "condiciones_rastro: list[tuple[list[Condicion], float]] = None, "
            )
        elif c is Sonoro:
            partes.append("")
        #
        elif c is Agarrable:
            partes.append("agarrado_por: Elemento, ")
        elif c is Consumible:
            partes.append("")
        elif c is Contenedor:
            partes.append("capacidad: float, ")
            partes_opcionales.append("contenido: list[Elemento] = None, ")
        elif c is Crafteable:
            partes.append("receta_para: tuple[str, list[Elemento]], ")
        elif c is Destruible:
            partes.append("durabilidad_max: float, ")
            partes_opcionales.append("durabilidad_actual: float = None, ")
        elif c is Equipable:
            partes_opcionales.append(
                "provoca_equiparlo: dict[Elemento, Accion] = None, equipado_por: Elemento = None, "
            )
        elif c is Golpeable:
            partes.append("")
        elif c is Ingrediente:
            partes.append("recetas_de: dict[str, Crafteable], ")
        elif c is Interactuable:
            partes.append("")
        elif c is Plantable:
            partes_opcionales.append("plantado: bool = False, ")
        elif c is Recolectable:
            partes_opcionales.append(
                "contenido: dict[str, tuple[Elemento, float]] = None, "
            )
        #
        elif c is Combinable:
            partes.append("elemento_combinable: Elemento, ")
            partes_opcionales.append("cantidad_max_combinable: float = None, ")
        elif c is Divisible:
            partes.append("cantidad_minima_divisible: float, ")
        elif c is Erosionable:
            partes.append(
                "condiciones_erosion: list[tuple[list[Condicion], float]], durabilidad_max_erosion: float, "
            )
            partes_opcionales.append("durabilidad_actual_erosion: float = None, ")
        elif c is Gaseoso:
            partes.append("")
        elif c is Liquido:
            partes.append("")
        elif c is Solido:
            partes.append("")
        elif c is Tangible:
            partes.append("")
        elif c is Transformable:
            partes.append("dict_transformable: dict[Condicion, Elemento], ")
        elif c is Transparente:
            partes.append("")
        #
        elif c is Comestible:
            partes.append("")
        elif c is Hidratante:
            partes.append("valor_hidratacion: float, ")
        elif c is Medicinal:
            partes.append("valor_medicinal: float, ")
        elif c is Nutritivo:
            partes.append("valor_nutritivo: float, ")
        elif c is Regenerable:
            partes.append("tasas_regeneracion: list[tuple[Stat, float]], ")
        elif c is Toxico:
            partes.append("valor_toxico: float, ")
        #
        elif c is Intercambiable:
            partes.append("")
        #
        elif c is Caduco:
            partes.append("duracion_max_caduco: int, ")
            partes_opcionales.append("duracion_restante_caduco: int = None, ")
        elif c is Estacional:
            partes.append("acciones_por_estacion: dict[Estacion, list[Accion]], ")
        elif c is Latente:
            partes.append("condiciones: list[Condicion], accion_latente: Accion, ")
        elif c is Perecedero:
            partes.append(
                "tiempo_maximo_perecedero: float, condiciones_perecedero: list[tuple[list[Condicion], float]], "
            )
            partes_opcionales.append("tiempo_actual_perecedero: float = None, ")
        elif c is Temporal:
            partes.append("")
        #
    partes_opcionales.append("\n")
    return "".join(partes + partes_opcionales)


print(
    get_parametros(
        [
            Peso,
            Consumible,
            Volumen,
            Ingrediente,
            Combinable,
            Divisible,
            Solido,
            Liquido,
            Gaseoso,
            Tangible,
            Transformable,
            Transparente,
            Comestible,
            Hidratante,
            Color,
            Medicinal,
            Toxico,
            Nutritivo,
            Perecedero,
        ]
    )
)
