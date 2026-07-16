# Core/Entitites/Elementos/Simples/Bot/bot.py

# el elemento bot se encuentra en etapa muy temprana e incompleta

from typing import Tuple
from Core.Entities.Comportamiento.Stats.stat import Stat
from Core.Entities.Comportamiento.comportamiento import Comportamiento
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
from Exceptions.exceptions import NumAtributosIncorrecto

comportamientos = Comportamiento.declarar_comportamientos(
    Peso,
    Volumen,
    Solido,
    Tangible,
    Color,
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
    #
    # _Complejos_____________________________________________________
    Agresividad,
    Armadura,
    Grasa,
    Longevidad,
    Movilidad,
    Percepcion,
    Tamanho,
    Temperatura_Optima,
    #
    # _Temporales____________________________________________________
    Focus,
    Hambre,
    Herida,
    #
    # _Simples_______________________________________________________
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

informacion = Comportamiento.declarar_comportamientos(
    ID,
    Apellidos,
)


def generarApellidos(ape1, ape2):
    apellidos = []
    for i in range(int(len(ape1) / 2)):
        apellidos.append(ape1[i])
        apellidos.append(ape2[i])
    return apellidos


class Bot(Elemento_Simple, comportamientos, stats, informacion):
    """
    ----------------------------------------------------------------------------



    ---- STATS COMPLEJOS -------------------------------------------------------
    self.stats["tamanho"]            -   ↑(atk, def, vida, energia)        ↓(velocidad, sigilo)
    self.stats["grasa"] = 0  #       -   ↑(energia)                        ↓(velocidad, regeneracion)
    self.stats["movilidad"]          -   ↑(atk, velocidad, regeneracion)   ↓(energia)
    self.stats["percepcion"]         -   ↑(deteccion)                      ↓(regeneracion)
    self.stats["armadura"]           -   ↑(def)                            ↓(regeneracion, atk, sigilo)
    self.stats["metabolismo"]        -   ↑(curacion, regeneracion,
                                           velocidad)                      ↓(vida, edad_adulta)
    self.stats["agresividad"]        -   ↑(atk)                            ↓(sigilo)
    self.stats["longevidad"]         -   ↑(edad_adulta, vida)              ↓(curacion, regeneracion, velocidad)
    self.stats["temperatura_optima"] -   ↑(curacion, regeneracion)         ↓(energia, edad_adulta)
    ----------------------------------------------------------------------------



    ---- MODIFICADORES ---------------------------------------------------------
    self.stats["heridas"] = (0    #       -   ↑()             ↓(vida, energia)# )
    self.stats["focus"] = 0       #       -   ↑(percepcion)   ↓()
    self.stats["hambre"] = 0      #       -   ↑()             ↓(energia)
    ----------------------------------------------------------------------------




    self.stats["vida"] = -1  # tamanho, metabolismo, longevidad
    self.stats["energia"] = -1  # tamanho, grasa, movilidad
    self.stats["curacion"]  # metabolismo, longevidad
    self.stats["regeneracion"] = -1  # grasa, movilidad, percepcion,
    #                                # armadura, longevidad
    self.stats["velocidad"] = -1  # tamanho, grasa,
    #                             # movilidad, metabolismo, longevidad
    self.stats["atk"] = -1  # tamanho, movilidad, armadura, agresividad
    self.stats["def"] = -1  # tamanho, armadura
    self.stats["deteccion"] = -1  # percepcion
    self.stats["sigilo"] = -1  # tamanho, armadura
    self.stats["edad_adulta"] = -1  #

    self.stats["tamanho"] = stats["tamanho"]
    self.stats["movilidad"] = stats["movilidad"]
    self.stats["percepcion"] = stats["percepcion"]
    self.stats["armadura"] = stats["armadura"]
    self.stats["metabolismo"] = stats["metabolismo"]
    self.stats["agresividad"] = stats["agresividad"]
    self.stats["longevidad"] = stats["longevidad"]
    """

    def __init__(
        self,
        id,
        tamanho: int,
        casilla,
        rotacion: float,
        capa: int = 2,
    ):
        super().__init__(
            Bot,
            id=id,
            tamanho=tamanho,
            casilla=casilla,
            capa=capa,
            rotacion=rotacion,
        )

    def set_casilla(self, new_casilla: Tuple[int, int]):
        self.casilla = new_casilla

    def set_rotacion(self, rotacion):
        self.rotacion = rotacion

    def serializar_adn(self):
        return self.adn

    

    def serialize_all(self):
        return {
            "id": self.id,
            "tamanho": self.serialize_tamanho(),
            "casilla": self.serialize_casilla(),
            "rotacion": self.serialize_rotacion(),
            "adn": self.serializar_adn(),
            "stats": Stat.serializar(self)
        }

    def serialize_position(self):
        return {
            "id": self.id,
            "tamanho": self.serialize_tamanho(),
            "casilla": self.serialize_casilla(),
            "rotacion": self.serialize_rotacion(),
        }
