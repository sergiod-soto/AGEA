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


def get_parametros_init(comportamientos: list[Comportamiento]):
    partes = []
    partes_opcionales = []
    partes.append("\n")
    for c in comportamientos:
        if c is Combustible:
            partes.append(
                "#Combustible:\nenergia_maxima: float, ratio_emision: float,   "
            )
            partes_opcionales.append(
                "#Combustible:\nenergia_actual: float = None, ratio_recarga: float = 0.0,"
            )
        elif c is Termico:
            partes.append(
                "#Termico:\ntemperatura_propia: float, tasa_transferencia: float, radio_termico: float, "
            )
        #
        elif c is Empujable:
            partes.append("")
        elif c is Enterrable:
            partes.append("\n#Enterrable:\ncoste_empujar: float, ")
        elif c is Flotable:
            partes.append("")
        elif c is Humedo:
            partes.append("\n#Humedo:\nhumedad_max: float, ")
        elif c is Inflamable:
            partes.append("\n#Inflamable:\ntemperatura_ignicion: float, ")
        elif c is Peso:
            partes.append("\n#Peso:\npeso: float, ")
        elif c is Volumen:
            partes.append("\n#Volumen:\nvolumen: float, ")
        #
        elif c is Color:
            partes.append("\n#Color:\nrgb_color: tuple[int, int, int], ")
        elif c is Luminoso:
            partes.append("\n#Luminoso:\ndistancia_luz: float, ")
            partes_opcionales.append("\n#Luminoso:\narea_luz: int = 360, ")
        elif c is Rastreable:
            partes_opcionales.append(
                "\n#Rastreable:\ncondiciones_rastro: list[tuple[list[Condicion], float]] = None, "
            )
        elif c is Sonoro:
            partes.append("")
        #
        elif c is Agarrable:
            partes.append("\n#Agarrable:\nagarrado_por: Elemento, ")
        elif c is Consumible:
            partes.append("")
        elif c is Contenedor:
            partes.append("\n#Contenedor:\ncapacidad: float, ")
            partes_opcionales.append(
                "\n#Contenedor:\ncontenido_contenedor: list[Elemento] = None, "
            )
        elif c is Crafteable:
            partes.append("\n#Crafteable:\nreceta_para: tuple[str, list[Elemento]], ")
        elif c is Destruible:
            partes.append("\n#Destruible:\ndurabilidad_max: float, ")
            partes_opcionales.append(
                "\n#Destruible:\ndurabilidad_actual: float = None, "
            )
        elif c is Equipable:
            partes_opcionales.append(
                "\n#Equipable:\nprovoca_equiparlo: dict[Elemento, Accion] = None, equipado_por: Elemento = None, "
            )
        elif c is Golpeable:
            partes.append("")
        elif c is Ingrediente:
            partes.append("\n#Ingrediente:\nrecetas_de: dict[str, Crafteable], ")
        elif c is Interactuable:
            partes.append("")
        elif c is Plantable:
            partes_opcionales.append("\n#Plantable:\nplantado: bool = False, ")
        elif c is Recolectable:
            partes_opcionales.append(
                "\n#Recolectable:\ncontenido_recolectable: dict[str, tuple[Elemento, float]] = None, "
            )
        #
        elif c is Combinable:
            partes_opcionales.append(
                "\n#Combinable:\ncantidad_max_combinable: float = None, "
            )
        elif c is Divisible:
            partes.append("\n#Divisible:\ncantidad_minima_divisible: float,")
        elif c is Erosionable:
            partes.append(
                "\n#Erosionable:\ncondiciones_erosion: list[tuple[list[Condicion], float]], durabilidad_max_erosion: float, "
            )
            partes_opcionales.append(
                "\n#Erosionable:\ndurabilidad_actual_erosion: float = None, "
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
            partes.append(
                "\n#Transformable:\ndict_transformable: dict[Condicion, Elemento], "
            )
        elif c is Transparente:
            partes.append("")
        #
        elif c is Comestible:
            partes.append("")
        elif c is Hidratante:
            partes.append("\n#Hidratante:\nvalor_hidratacion: float, ")
        elif c is Medicinal:
            partes.append("\n#Medicinal:\nvalor_medicinal: float, ")
        elif c is Nutritivo:
            partes.append("\n#Nutritivo:\nvalor_nutritivo: float, ")
        elif c is Regenerable:
            partes.append(
                "\n#Regenerable:\ntasas_regeneracion: list[tuple[Stat, float]], "
            )
        elif c is Toxico:
            partes.append("\n#Toxico:\nvalor_toxico: float, ")
        #
        elif c is Intercambiable:
            partes.append("")
        #
        elif c is Caduco:
            partes.append("\n#Caduco:\nduracion_max_caduco: int, ")
            partes_opcionales.append(
                "\n#Caduco:\nduracion_restante_caduco: int = None, "
            )
        elif c is Estacional:
            partes.append(
                "\n#Estacional:\nacciones_por_estacion: dict[Estacion, list[Accion]], "
            )
        elif c is Latente:
            partes.append(
                "\n#Latente:\ncondiciones: list[Condicion], accion_latente: Accion, "
            )
        elif c is Perecedero:
            partes.append(
                "\n#Perecedero:\ntiempo_maximo_perecedero: float, condiciones_perecedero: list[tuple[list[Condicion], float]], "
            )
            partes_opcionales.append(
                "\n#Perecedero:\ntiempo_actual_perecedero: float = None, "
            )
        elif c is Temporal:
            partes.append("")
        #
    partes_opcionales.append("\n")
    return "".join(partes + partes_opcionales)


def get_parametros_superinit(comportamientos: list[Comportamiento]):
    partes = []
    partes_opcionales = []
    partes.append("\n")
    for c in comportamientos:
        if c is Combustible:
            partes.append(
                "#Combustible:\nenergia_maxima = energia_maxima, ratio_emision = ratio_emision,   "
            )
            partes_opcionales.append(
                "#Combustible:\nenergia_actual = energia_actual, ratio_recarga = ratio_recarga, "
            )
        elif c is Termico:
            partes.append(
                "#Termico:\ntemperatura_propia = temperatura_propia, tasa_transferencia = tasa_transferencia, radio_termico = radio_termico, "
            )
        #
        elif c is Empujable:
            partes.append("")
        elif c is Enterrable:
            partes.append("\n#Enterrable:\ncoste_empujar = coste_empujar, ")
        elif c is Flotable:
            partes.append("")
        elif c is Humedo:
            partes.append("\n#Humedo:\nhumedad_max = humedad_max, ")
        elif c is Inflamable:
            partes.append(
                "\n#Inflamable:\ntemperatura_ignicion = temperatura_ignicion, "
            )
        elif c is Peso:
            partes.append("\n#Peso:\npeso = peso, ")
        elif c is Volumen:
            partes.append("\n#Volumen:\nvolumen = volumen, ")
        #
        elif c is Color:
            partes.append("\n#Color:\nrgb_color = rgb_color, ")
        elif c is Luminoso:
            partes.append("\n#Luminoso:\ndistancia_luz = distancia_luz, ")
            partes_opcionales.append("\n#Luminoso:\narea_luz = area_luz, ")
        elif c is Rastreable:
            partes_opcionales.append(
                "\n#Rastreable:\ncondiciones_rastro = condiciones_rastro,"
            )
        elif c is Sonoro:
            partes.append("")
        #
        elif c is Agarrable:
            partes.append("\n#Agarrable:\nagarrado_por = agarrado_por,")
        elif c is Consumible:
            partes.append("")
        elif c is Contenedor:
            partes.append("\n#Contenedor:\ncapacidad = capacidad,")
            partes_opcionales.append(
                "\n#Contenedor:\ncontenido_contenedor = contenido_contenedor,"
            )
        elif c is Crafteable:
            partes.append("\n#Crafteable:\nreceta_para = receta_para,")
        elif c is Destruible:
            partes.append("\n#Destruible:\ndurabilidad_max = durabilidad_max,")
            partes_opcionales.append(
                "\n#Destruible:\ndurabilidad_actual = durabilidad_actual,"
            )
        elif c is Equipable:
            partes_opcionales.append(
                "\n#Equipable:\nprovoca_equiparlo = provoca_equiparlo, equipado_por = equipado_por,"
            )
        elif c is Golpeable:
            partes.append("")
        elif c is Ingrediente:
            partes.append("\n#Ingrediente:\nrecetas_de = recetas_de,")
        elif c is Interactuable:
            partes.append("")
        elif c is Plantable:
            partes_opcionales.append("\n#Plantable:\nplantado = plantado,")
        elif c is Recolectable:
            partes_opcionales.append(
                "\n#Recolectable:\ncontenido_recolectable = contenido_recolectable,"
            )
        #
        elif c is Combinable:
            partes_opcionales.append(
                "\n#Combinable:\ncantidad_max_combinable = cantidad_max_combinable,"
            )
        elif c is Divisible:
            partes.append(
                "\n#Divisible:\ncantidad_minima_divisible = cantidad_minima_divisible,"
            )
        elif c is Erosionable:
            partes.append(
                "\n#Erosionable:\ncondiciones_erosion = condiciones_erosion, durabilidad_max_erosion = durabilidad_max_erosion,"
            )
            partes_opcionales.append(
                "\n#Erosionable:\ndurabilidad_actual_erosion = durabilidad_actual_erosion,"
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
            partes.append("\n#Transformable:\ndict_transformable = dict_transformable,")
        elif c is Transparente:
            partes.append("")
        #
        elif c is Comestible:
            partes.append("")
        elif c is Hidratante:
            partes.append("\n#Hidratante:\nvalor_hidratacion = valor_hidratacion,")
        elif c is Medicinal:
            partes.append("\n#Medicinal:\nvalor_medicinal = valor_medicinal,")
        elif c is Nutritivo:
            partes.append("\n#Nutritivo:\nvalor_nutritivo = valor_nutritivo,")
        elif c is Regenerable:
            partes.append("\n#Regenerable:\ntasas_regeneracion = tasas_regeneracion,")
        elif c is Toxico:
            partes.append("\n#Toxico:\nvalor_toxico = valor_toxico,")
        #
        elif c is Intercambiable:
            partes.append("")
        #
        elif c is Caduco:
            partes.append("\n#Caduco:\nduracion_max_caduco = duracion_max_caduco,")
            partes_opcionales.append(
                "\n#Caduco:\nduracion_restante_caduco = duracion_restante_caduco,"
            )
        elif c is Estacional:
            partes.append(
                "\n#Estacional:\nacciones_por_estacion = acciones_por_estacion,"
            )
        elif c is Latente:
            partes.append(
                "\n#Latente:\ncondiciones = condiciones, accion_latente = accion_latente,"
            )
        elif c is Perecedero:
            partes.append(
                "\n#Perecedero:\ntiempo_maximo_perecedero = tiempo_maximo_perecedero, condiciones_perecedero = condiciones_perecedero,"
            )
            partes_opcionales.append(
                "\n#Perecedero:\ntiempo_actual_perecedero = tiempo_actual_perecedero,"
            )
        elif c is Temporal:
            partes.append("")
        #
    partes_opcionales.append("\n")
    return "".join(partes + partes_opcionales)


"""
Ejemplo:

class Agua(Peso, Volumen, Temperatura):
    def __init__(self, temperatura: float, **kwargs):
    
        super().__init__(
            temperatura = temperatura,

            peso = 1.0,
            volumen = 1.0
            **kwargs #  <- Importante
        )
"""


print(
    "INIT:"
    + get_parametros_init(
        [
            Peso,
            Consumible,
            Volumen,
            Ingrediente,
            Combinable,
            Divisible,
            Liquido,
            Tangible,
            Transformable,
            Transparente,
            Comestible,
            Hidratante,
        ]
    )
    + "SUPER:"
    + get_parametros_superinit(
        [
            Peso,
            Consumible,
            Volumen,
            Ingrediente,
            Combinable,
            Divisible,
            Liquido,
            Tangible,
            Transformable,
            Transparente,
            Comestible,
            Hidratante,
        ]
    )
)
