from typing import Optional, Tuple
from Core.Entities.Comportamiento.Energetico.termico import Termico
from Core.Entities.Comportamiento.Fisico.empujable import Empujable
from Core.Entities.Comportamiento.Fisico.flotable import Flotable
from Core.Entities.Comportamiento.Fisico.peso import Peso
from Core.Entities.Comportamiento.Fisico.volumen import Volumen
from Core.Entities.Comportamiento.Informativo.color import Color
from Core.Entities.Comportamiento.Informativo.rastreable import Rastreable
from Core.Entities.Comportamiento.Interaccion.agarrable import Agarrable
from Core.Entities.Comportamiento.Interaccion.contenedor import Contenedor
from Core.Entities.Comportamiento.Interaccion.golpeable import Golpeable
from Core.Entities.Comportamiento.Interaccion.interactuable import Interactuable
from Core.Entities.Comportamiento.Material.solido import Solido
from Core.Entities.Comportamiento.Material.tangible import Tangible
from Core.Entities.Comportamiento.Salud.comestible import Comestible
from Core.Entities.Comportamiento.Salud.hidratante import Hidratante
from Core.Entities.Comportamiento.Salud.nutritivo import Nutritivo
from Core.Entities.Comportamiento.Salud.toxico import Toxico
from Core.Entities.Comportamiento.Stats.Complejos.agresividad import Agresividad
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
from Core.Entities.Comportamiento.Stats.Informacion.posicion import Posicion
from Core.Entities.Comportamiento.Stats.Modificadores.focus import Focus
from Core.Entities.Comportamiento.Stats.Modificadores.hambre import Hambre
from Core.Entities.Comportamiento.Stats.Modificadores.herida import Herida
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
from Core.Entities.Elementos.Simples.elemento_simple import Elemento_Simple
from Core.Entities.Elementos.Simples.Bot.controlador import obtener_siguiente_apellido
from Exceptions.exceptions import *
from Core.Entities.Comportamiento.comportamiento import Comportamiento

comportamientos = Comportamiento.declarar_comportamientos(
    Peso,
    Volumen,
    Solido,
    Tangible,
    Comestible,
    Hidratante,
    Color,
    Toxico,
    Nutritivo,
    Termico,
    Empujable,
    Flotable,
    Rastreable,
    Agarrable,
    Contenedor,
    Golpeable,
    Interactuable,
)

stats = Comportamiento.declarar_comportamientos(
    Agresividad,
    Armadura,
    Grasa,
    Longevidad,
    Movilidad,
    Percepcion,
    Tamanho,
    Temperatura_Optima,
    #
    Focus,
    Hambre,
    Herida,
    #
    Ataque,
    Defensa,
    Deteccion,
    Edad_Adulta,
    Edad,
    Energia,
    Regulacion_Temperatura,
    Sigilo,
    Temperatura,
    Velocidad,
    Vida,
)

informacion = Comportamiento.declarar_comportamientos(ID, Apellidos, Posicion)


stats_bots = [
    "adn",
    "padre",
    "madre",
    "apellido0",
    "apellido1",
    "apellido2",
    "apellido3",
    "x",
    "y",
]

def generarApellidos(ape1, ape2):
    apellidos = []
    for i in range(int(len(ape1) / 2)):
        apellidos.append(ape1[i])
        apellidos.append(ape2[i])
    return apellidos


class Bot(Elemento_Simple, comportamientos, stats, informacion):

    #   ----------------------------------------------------------------------------
    #
    #
    #
    #   ---- STATS COMPLEJOS -------------------------------------------------------
    #   self.stats["tamanho"]            -   ↑(atk, def, vida, energia)        ↓(velocidad, sigilo)
    #   self.stats["grasa"] = 0  #       -   ↑(energia)                         ↓(velocidad, regeneracion)
    #   self.stats["movilidad"]          -   ↑(atk, velocidad, regeneracion)   ↓(energia)
    #   self.stats["percepcion"]         -   ↑(deteccion)                      ↓(regeneracion)
    #   self.stats["armadura"]           -   ↑(def)                            ↓(regeneracion, atk, sigilo)
    #   self.stats["metabolismo"]        -   ↑(curacion, regeneracion,
    #                                          velocidad)                      ↓(vida, edad_adulta)
    #   self.stats["agresividad"]        -   ↑(atk)                            ↓(sigilo)
    #   self.stats["longevidad"]         -   ↑(edad_adulta, vida)              ↓(curacion, regeneracion, velocidad)
    #   self.stats["temperatura_optima"] -   ↑(curacion, regeneracion)         ↓(energia, edad_adulta)
    #   ----------------------------------------------------------------------------
    #
    #
    #
    #   ---- MODIFICADORES ---------------------------------------------------------
    # self.stats["heridas"] = (0    #       -   ↑()             ↓(vida, energia)# )
    # self.stats["focus"] = 0       #       -   ↑(percepcion)   ↓()
    # self.stats["hambre"] = 0      #       -   ↑()             ↓(energia)
    #   ----------------------------------------------------------------------------
    #
    #
    #
    #
    # self.stats["vida"] = -1  # tamanho, metabolismo, longevidad
    # self.stats["energia"] = -1  # tamanho, grasa, movilidad
    # self.stats["curacion"]  # metabolismo, longevidad
    # self.stats["regeneracion"] = -1  # grasa, movilidad, percepcion,
    # #                                # armadura, longevidad
    # self.stats["velocidad"] = -1  # tamanho, grasa,
    # #                             # movilidad, metabolismo, longevidad
    # self.stats["atk"] = -1  # tamanho, movilidad, armadura, agresividad
    # self.stats["def"] = -1  # tamanho, armadura
    # self.stats["deteccion"] = -1  # percepcion
    # self.stats["sigilo"] = -1  # tamanho, armadura
    # self.stats["edad_adulta"] = -1  #
    #
    # self.stats["tamanho"] = stats["tamanho"]
    # self.stats["movilidad"] = stats["movilidad"]
    # self.stats["percepcion"] = stats["percepcion"]
    # self.stats["armadura"] = stats["armadura"]
    # self.stats["metabolismo"] = stats["metabolismo"]
    # self.stats["agresividad"] = stats["agresividad"]
    # self.stats["longevidad"] = stats["longevidad"]
    #

    # class Stats:

    #     def to_JSON(self):
    #         json = {}
    #         for clave in self.stats:
    #             json[clave] = self.stats[clave]
    #         return json

    #     def serialize(self):

    #         json = "{"

    #         keys = list(self.stats.keys())
    #         for clave in keys:
    #             valor = self.stats[clave]
    #             if isinstance(valor, str):
    #                 valor = f'"{valor}"'
    #             json += f'"{clave}": {valor}'

    #             if clave != keys[-1]:  # si no es la última clave
    #                 json += ","
    #         json += "}"
    #         return json

    def __init__(
        self,
        padres: Tuple[str, str] | None,
        tamanho: int,
        casilla,
        rotacion: float,
        capa: int = 2,
    ):
        super().__init__(
            Bot,
            tamanho,
            casilla,
            capa,
            rotacion,
        )

        if (padres is not None) and (len(padres) != 2):
            raise ValueError("padres debe ser una tupla con exactamente 2 Bots o None")

        #
        #
        #
        visibilidad = 1
        #
        #

        self.padres = padres

        if padres["padre"] == None:
            if padres["madre"] == None:
                apellido = self.inicializar_apellido()
                self.apellidos = [
                    apellido,
                    apellido,
                    apellido,
                    apellido,
                ]
                padres["padre"] = ""
                padres["madre"] = ""
            else:
                self.apellidos = padres["madre"].apellido
        else:
            if padres["madre"] == None:
                self.apellidos = padres["padre"].apellido
            else:
                self.apellidos = generarApellidos(padres["padre"], padres["madre"])
                self.padres = {
                    "padre": padres["padre"],
                    "madre": padres["madre"],
                }


        self.casilla = casilla

        #
        #
        #
        # ---- inicializacion de stats   -----------------------------------------
        try:
            self.stats = self.Stats(stats)
        except NumAtributosIncorrecto:
            print("ERROR CON LOS STATS")

    def inicializar_apellido(self):
        return obtener_siguiente_apellido()

    def set_casilla(self, new_casilla: Tuple[int, int]):
        self.stats = new_casilla

    def set_rotacion(self, rotacion):
        self.rotacion = rotacion

    def serializar_adn(self):
        return self.adn

    def serializar_apellidos(self):
        apellidos = []
        for apellido in self.apellidos:
            apellidos.append(apellido)
        return apellidos

    def serializar_padres(self):
        return {
            "padre": self.padres["padre"] if self.padres else None,
            "madre": self.padres["madre"] if self.padres else None,
        }

    def serialize_all(self):
        return str(
            {
                "id": self.id,
                "tamanho": self.serialize_tamanho(),
                "distancia_visible": self.serialize_distancia_visible(),
                "casilla": self.serialize_casilla(),
                "rotacion": self.serialize_rotacion(),
                "apellidos": self.serializar_apellidos(),
                "adn": self.serializar_adn(),
                "stats": self.stats.serialize(),
                "padres": self.serializar_padres(),
            }
        )

    def serialize_position(self):
        return str(
            {
                "id": self.id,
                "tamanho": self.serialize_tamanho(),
                "distancia_visible": self.serialize_distancia_visible(),
                "casilla": self.serialize_casilla(),
                "rotacion": self.serialize_rotacion(),
            }
        )
