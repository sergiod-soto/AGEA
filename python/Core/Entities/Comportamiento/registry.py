# Core/entities/Comportamiento/registry.py

from Core.Entities.Comportamiento.Energetico.combustible import Combustible
from Core.Entities.Comportamiento.Energetico.energetico import Energetico
from Core.Entities.Comportamiento.Energetico.termico import Termico
from Core.Entities.Comportamiento.Fisico.empujable import Empujable
from Core.Entities.Comportamiento.Fisico.enterrable import Enterrable
from Core.Entities.Comportamiento.Fisico.fisico import Fisico
from Core.Entities.Comportamiento.Fisico.flotable import Flotable
from Core.Entities.Comportamiento.Fisico.humedo import Humedo
from Core.Entities.Comportamiento.Fisico.inflamable import Inflamable
from Core.Entities.Comportamiento.Fisico.peso import Peso
from Core.Entities.Comportamiento.Fisico.volumen import Volumen
from Core.Entities.Comportamiento.Informativo.color import Color
from Core.Entities.Comportamiento.Informativo.informativo import Informativo
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
from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Comportamiento.Interaccion.interactuable import Interactuable
from Core.Entities.Comportamiento.Interaccion.plantable import Plantable
from Core.Entities.Comportamiento.Interaccion.recolectable import Recolectable
from Core.Entities.Comportamiento.Material.combinable import Combinable
from Core.Entities.Comportamiento.Material.divisible import Divisible
from Core.Entities.Comportamiento.Material.erosionable import Erosionable
from Core.Entities.Comportamiento.Material.gaseoso import Gaseoso
from Core.Entities.Comportamiento.Material.liquido import Liquido
from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Comportamiento.Material.solido import Solido
from Core.Entities.Comportamiento.Material.tangible import Tangible
from Core.Entities.Comportamiento.Material.transformable import Transformable
from Core.Entities.Comportamiento.Salud.comestible import Comestible
from Core.Entities.Comportamiento.Salud.hidratante import Hidratante
from Core.Entities.Comportamiento.Salud.medicinal import Medicinal
from Core.Entities.Comportamiento.Salud.nutritivo import Nutritivo
from Core.Entities.Comportamiento.Salud.salud import Salud
from Core.Entities.Comportamiento.Stats.tiene_stats import Tiene_Stats
from Core.Entities.Comportamiento.Temporal.regenerable import Regenerable
from Core.Entities.Comportamiento.Salud.toxico import Toxico
from Core.Entities.Comportamiento.Social.intercambiable import Intercambiable
from Core.Entities.Comportamiento.Social.social import Social
from Core.Entities.Comportamiento.Stats.Complejos.armadura import Armadura
from Core.Entities.Comportamiento.Stats.Complejos.grasa import Grasa
from Core.Entities.Comportamiento.Stats.Complejos.longevidad import Longevidad
from Core.Entities.Comportamiento.Stats.Complejos.movilidad import Movilidad
from Core.Entities.Comportamiento.Stats.Complejos.percepcion import Percepcion
from Core.Entities.Comportamiento.Stats.Complejos.tamanho import Tamanho
from Core.Entities.Comportamiento.Stats.Complejos.temperatura_optima import (
    Temperatura_Optima,
)
from Core.Entities.Comportamiento.Stats.Informacion.apellidos import Apellidos
from Core.Entities.Comportamiento.Stats.Informacion.id import ID
from Core.Entities.Comportamiento.Stats.Modificadores.focus import Focus
from Core.Entities.Comportamiento.Stats.Modificadores.hambre import Hambre
from Core.Entities.Comportamiento.Stats.Modificadores.herida import Herida
from Core.Entities.Comportamiento.Stats.Modificadores.modificador import Modificador
from Core.Entities.Comportamiento.Stats.Simples.ataque import Ataque
from Core.Entities.Comportamiento.Stats.Simples.defensa import Defensa
from Core.Entities.Comportamiento.Stats.Simples.deteccion import Deteccion
from Core.Entities.Comportamiento.Stats.Simples.edad import Edad
from Core.Entities.Comportamiento.Stats.Simples.edad_adulta import Edad_Adulta
from Core.Entities.Comportamiento.Stats.Simples.energia import Energia
from Core.Entities.Comportamiento.Stats.Simples.regulacion_temperatura import (
    Regulacion_Temperatura,
)
from Core.Entities.Comportamiento.Stats.Simples.sigilo import Sigilo
from Core.Entities.Comportamiento.Stats.Simples.temperatura import Temperatura
from Core.Entities.Comportamiento.Stats.Simples.velocidad import Velocidad
from Core.Entities.Comportamiento.Stats.Simples.vida import Vida
from Core.Entities.Comportamiento.Stats.stat import Stat
from Core.Entities.Comportamiento.Temporal.caduco import Caduco
from Core.Entities.Comportamiento.Temporal.estacional import Estacional
from Core.Entities.Comportamiento.Temporal.latente import Latente
from Core.Entities.Comportamiento.Temporal.perecedero import Perecedero
from Core.Entities.Comportamiento.Temporal.temporal import Temporal
from Core.Entities.Comportamiento.Terreno.arenoso import Arenoso
from Core.Entities.Comportamiento.Terreno.herboso import Hervoso
from Core.Entities.Comportamiento.Terreno.encharcado import Encharcado
from Core.Entities.Comportamiento.Terreno.helado import Helado
from Core.Entities.Comportamiento.Terreno.embarrado import Embarrado
from Core.Entities.Comportamiento.Terreno.terroso import Terroso


from Core.Entities.Comportamiento.Terreno.gravoso import Gravoso
from Core.Entities.Comportamiento.Terreno.rocoso import Rocoso
from Core.Entities.Comportamiento.Terreno.terreno import Terreno
from Core.Entities.Comportamiento.comportamiento import Comportamiento

import logging

from Core.Entities.Comportamiento.comportamiento_test import Comportamiento_Test

logger = logging.getLogger(__name__)

COMPORTAMIENTOS: dict[str, type] = {
    # A
    "Agarrable": Agarrable,
    "Apellidos": Apellidos,
    "Arenoso": Arenoso,
    "Armadura": Armadura,
    "Ataque": Ataque,
    # B
    "Embarrado": Embarrado,
    # C
    "Caduco": Caduco,
    "Color": Color,
    "Combinable": Combinable,
    "Combustible": Combustible,
    "Comestible": Comestible,
    "Comportamiento": Comportamiento,
    "Comportamiento_Test": Comportamiento_Test,
    "Consumible": Consumible,
    "Contenedor": Contenedor,
    "Crafteable": Crafteable,
    # D
    "Defensa": Defensa,
    "Destruible": Destruible,
    "Deteccion": Deteccion,
    "Divisible": Divisible,
    # E
    "Empujable": Empujable,
    "Encharcado": Encharcado,
    "Enterrable": Enterrable,
    "Energetico": Energetico,
    "Equipable": Equipable,
    "Erosionable": Erosionable,
    "Edad": Edad,
    "Edad_Adulta": Edad_Adulta,
    "Energia": Energia,
    "Estacional": Estacional,
    # F
    "Fisico": Fisico,
    "Flotable": Flotable,
    "Focus": Focus,
    # G
    "Golpeable": Golpeable,
    "Gaseoso": Gaseoso,
    "Grasa": Grasa,
    "Gravoso": Gravoso,
    # H
    "Hambre": Hambre,
    "Helado": Helado,
    "Herida": Herida,
    "Hervoso": Hervoso,
    "Hidratante": Hidratante,
    "Humedo": Humedo,
    # I
    "ID": ID,
    "Inflamable": Inflamable,
    "Informativo": Informativo,
    "Ingrediente": Ingrediente,
    "Interaccion": Interaccion,
    "Interactuable": Interactuable,
    "Intercambiable": Intercambiable,
    # J
    # K
    # L
    "Latente": Latente,
    "Liquido": Liquido,
    "Longevidad": Longevidad,
    "Luminoso": Luminoso,
    # M
    "Material": Material,
    "Medicinal": Medicinal,
    "Modificador": Modificador,
    "Movilidad": Movilidad,
    # N
    "Nutritivo": Nutritivo,
    # O
    # P
    "Percepcion": Percepcion,
    "Perecedero": Perecedero,
    "Peso": Peso,
    "Plantable": Plantable,
    # Q
    # R
    "Rastreable": Rastreable,
    "Recolectable": Recolectable,
    "Regenerable": Regenerable,
    "Regulacion_Temperatura": Regulacion_Temperatura,
    "Rocoso": Rocoso,
    # S
    "Salud": Salud,
    "Sigilo": Sigilo,
    "Social": Social,
    "Solido": Solido,
    "Sonoro": Sonoro,
    "Stat": Stat,
    # T
    "Tamanho": Tamanho,
    "Tangible": Tangible,
    "Temperatura": Temperatura,
    "Temperatura_Optima": Temperatura_Optima,
    "Temporal": Temporal,
    "Termico": Termico,
    "Terreno": Terreno,
    "Terroso": Terroso,
    "Tiene_Stats": Tiene_Stats,
    "Toxico": Toxico,
    "Transformable": Transformable,
    # U
    # V
    "Velocidad": Velocidad,
    "Vida": Vida,
    "Volumen": Volumen,
    # W
    # X
    # Y
    # Z
}


def _todas_las_subclases(cls: type) -> set[type]:
    """
    Recorre __subclasses__() recursivamente: Python solo expone las
    subclases DIRECTAS con __subclasses__(), así que para encontrar
    nietas (subclases de subclases) hay que bajar recursivamente.
    """
    directas = set(cls.__subclasses__())
    return directas | {
        nieta for hija in directas for nieta in _todas_las_subclases(hija)
    }


def _avisar_si_falta_registrar():

    reales = {
        c for c in _todas_las_subclases(Comportamiento) if c._es_comportamiento_real()
    }
    registradas = set(COMPORTAMIENTOS.values())
    faltantes = reales - registradas
    if faltantes:
        nombres = ", ".join(sorted(c.__name__ for c in faltantes))
        logger.warning(
            "COMPORTAMIENTOS: hay comportamiento(s) definidos pero sin "
            "registrar (no se podrán reconstruir desde snapshot/red hasta "
            "que se añadan): %s",
            nombres,
        )


_avisar_si_falta_registrar()
