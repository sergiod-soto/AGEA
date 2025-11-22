from typing import Optional, Tuple
from Core.Entities.Elemento import Elemento
from Core.Entities.Elementos.Simples.Bot import Controlador
from Exceptions import *


stats_bots = [
    "id",
    "adn",
    "apellido0",
    "apellido1",
    "apellido2",
    "apellido3",
    "x",
    "y",
    "vida",
    "energia",
    "curacion",
    "regeneracion",
    "velocidad",
    "atk",
    "def",
    "deteccion",
    "sigilo",
    "edad",
    "edad_adulta",
    "temperatura",
    "regulacion_temperatura",
    "tamanho",
    "grasa",
    "movilidad",
    "percepcion",
    "armadura",
    "metabolismo",
    "agresividad",
    "longevidad",
    "temperatura_optima",
    "heridas",
    "focus",
    "hambre",
    "padre",
    "madre",
]


def generarApellidos(ape1, ape2):
    apellidos = []
    for i in range(int(len(ape1) / 2)):
        apellidos.append(ape1[i])
        apellidos.append(ape2[i])
    return apellidos


class Bot(Elemento):

    class Stats:

        def __init__(self, numeros):
            #
            #
            #   ---- STATS (INICIALIZACION) -----------------------------------------------------------------
            self.stats = {}
            #   ----------------------------------------------------------------------------
            #
            #
            #   ---- STATS BASE (INICIALIZACION) ------------------------------------------------------------
            self.stats["vida"] = -1
            self.stats["energia"] = -1
            self.stats["curacion"] = -1
            self.stats["regeneracion"] = -1
            self.stats["velocidad"] = -1
            self.stats["atk"] = -1
            self.stats["def"] = -1
            self.stats["deteccion"] = -1
            self.stats["sigilo"] = -1
            self.stats["edad"] = -1
            self.stats["edad_adulta"] = -1
            self.stats["temperatura"] = -1
            self.stats["regulacion_temperatura"] = -1
            #   ----------------------------------------------------------------------------
            #
            #
            #
            #   ---- STATS COMPLEJOS (INICIALIZACION) -------------------------------------------------------
            self.stats["tamanho"] = -1
            self.stats["grasa"] = -1
            self.stats["movilidad"] = -1
            self.stats["percepcion"] = -1
            self.stats["armadura"] = -1
            self.stats["metabolismo"] = -1
            self.stats["agresividad"] = -1
            self.stats["longevidad"] = -1
            self.stats["temperatura_optima"] = -1
            #   ----------------------------------------------------------------------------
            #
            #
            #
            #   ---- MODIFICADORES (INICIALIZACION) ---------------------------------------------------------
            self.stats["heridas"] = -1
            self.stats["focus"] = -1
            self.stats["hambre"] = -1

            numAtributos = len(self.stats)
            if len(numeros) != numAtributos:
                raise NumAtributosIncorrecto(
                    f"""Numero de atributos esperados generando stats: {numAtributos}, encontrados: {len(numeros)}"""
                )
            #   ----------------------------------------------------------------------------
            #   ----------------------------------------------------------------------------
            #
            #
            #
            #
            #
            #
            #
            #
            #
            #
            #
            #   ---- STATS BASE ------------------------------------------------------------
            self.stats["vida"] = numeros[
                "vida"
            ]  # (una orquilla alrededor de este valor)
            self.stats["energia"] = numeros["energia"]
            self.stats["curacion"] = numeros["curacion"]
            self.stats["regeneracion"] = numeros["regeneracion"]
            self.stats["velocidad"] = numeros["velocidad"]
            self.stats["atk"] = numeros["atk"]
            self.stats["def"] = numeros["def"]
            self.stats["deteccion"] = numeros[
                "deteccion"
            ]  # (area de deteccion de comida, bots, etc)
            self.stats["sigilo"] = numeros["sigilo"]
            self.stats["edad"] = numeros["edad"]
            self.stats["edad_adulta"] = numeros[
                "edad_adulta"
            ]  # (cuando puede empezar a reproducirse)
            self.stats["temperatura"] = numeros["temperatura"]
            self.stats["regulacion_temperatura"] = numeros["regulacion_temperatura"]
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
            self.stats["heridas"] = (
                0  #         -   ↑()                     ↓(vida, energia)
            )
            self.stats["focus"] = 0  #         -   ↑(percepcion)           ↓()
            self.stats["hambre"] = 0  #         -   ↑()                     ↓(energia)
            #   ----------------------------------------------------------------------------
            #
            #
            #
            #
            #   TODO
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

        def to_JSON(self):
            json = {}
            for clave in self.stats:
                json[clave] = self.stats[clave]
            return json

        def serialize(self):

            json = "{"

            keys = list(self.stats.keys())
            for clave in keys:
                valor = self.stats[clave]
                if isinstance(valor, str):
                    valor = f'"{valor}"'
                json += f'"{clave}": {valor}'

                if clave != keys[-1]:  # si no es la última clave
                    json += ","
            json += "}"
            return json

            # datos = []

            # for stat in stats_bots:
            #     datos.append(self.stats[stat])

    def __init__(
        self, id: str, adn, stats: Stats, padres: Optional[Tuple[str, str]], casilla
    ):
        if (padres is not None) and (len(padres) != 2):
            raise ValueError("padres debe ser una tupla con exactamente 2 Bots o None")

        #
        #
        #
        visibilidad = 1
        super().__init__("bot", visibilidad, casilla)
        #
        #

        self.tipo = "bot"
        self.id = id
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

        self.adn = adn

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
        return Controlador.obtener_siguiente_apellido()

    def set_casilla(self, new_casilla: Tuple[int, int]):
        self.casilla = new_casilla

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
        return {
            "id": self.id,
            "casilla": self.serialize_casilla(),
            "rotacion": self.serialize_rotacion(),
            "apellidos": self.serializar_apellidos(),
            "adn": self.adn,
            "stats": self.stats.serialize(),
            "padres": self.serializar_padres(),
        }

    def serialize_position(self):
        return {
            "id": self.id,
            "casilla": self.serialize_casilla(),
            "rotacion": self.serialize_rotacion(),
        }
