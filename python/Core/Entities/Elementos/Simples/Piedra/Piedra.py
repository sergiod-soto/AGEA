from enum import Enum
from typing import Callable

from Core.Entities.Comportamiento.Energetico.termico import Termico
from Core.Entities.Comportamiento.Fisico.empujable import Empujable
from Core.Entities.Comportamiento.Fisico.enterrable import Enterrable
from Core.Entities.Comportamiento.Fisico.peso import Peso
from Core.Entities.Comportamiento.Fisico.volumen import Volumen
from Core.Entities.Comportamiento.Informativo.color import Color
from Core.Entities.Comportamiento.Informativo.sonoro import Sonoro
from Core.Entities.Comportamiento.Interaccion.agarrable import Agarrable
from Core.Entities.Comportamiento.Interaccion.crafteable import Crafteable
from Core.Entities.Comportamiento.Interaccion.destruible import Destruible
from Core.Entities.Comportamiento.Interaccion.golpeable import Golpeable
from Core.Entities.Comportamiento.Interaccion.ingrediente import Ingrediente
from Core.Entities.Comportamiento.Material.erosionable import Erosionable
from Core.Entities.Comportamiento.Material.solido import Solido
from Core.Entities.Comportamiento.Material.tangible import Tangible
from Core.Entities.Comportamiento.Social.intercambiable import Intercambiable
from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion
from Core.Entities.Elementos.Simples.elemento_simple import Elemento_Simple
from Core.Entities.Elementos.elemento import Elemento
from Exceptions.Bot.comportamientos_exceptions import Peso_Zero

#
# las piedras son elementos que pueden ser movidas a cambio de energia, no
# decaen a lo largo del tiempo.
#
#


comportamientos = Comportamiento.declarar_comportamientos(
    Peso,
    Enterrable,
    Empujable,
    Volumen,
    Ingrediente,
    Color,
    Agarrable,
    Destruible,
    Golpeable,
    Solido,
    Tangible,
    Termico,
    Erosionable,
    Intercambiable,
    Sonoro,
)


class Piedra(Elemento_Simple, comportamientos):

    def __init__(
        self,
        tamanho: int,
        casilla: tuple[int, int],
        capa: int,
        #
        # Peso:
        peso: float,
        # Enterrable:
        coste_empujar: float,
        # Volumen:
        volumen: float,
        # Ingrediente:
        recetas_de: dict[str, Crafteable],
        # Color:
        rgb_color: tuple[int, int, int],
        # Agarrable:
        agarrado_por: Elemento,
        # Destruible:
        durabilidad_max: float,
        # Termico:
        temperatura_propia: float,
        tasa_transferencia: float,
        radio_termico: float,
        # Erosionable:
        condiciones_erosion: list[tuple[list[Condicion], float]],
        durabilidad_max_erosion: float,
        # Destruible:
        durabilidad_actual: float = None,
        # Erosionable:
        durabilidad_actual_erosion: float = None,
        #
        rotacion: int = 0,
        fuerza_sector_activo=False,
        fuerza_vecinos_activos=False,
        **kwargs
    ):
        # comprobaciones:
        if peso == 0:
            raise Peso_Zero()
        
        super().__init__(
            tipo=Piedra,
            tamanho=tamanho,
            casilla=casilla,
            capa=capa,
            rotacion=rotacion,
            fuerza_sector_activo=fuerza_sector_activo,
            fuerza_vecinos_activos=fuerza_vecinos_activos,
            # Peso:
            peso=peso,
            # Enterrable:
            coste_empujar=coste_empujar,
            # Volumen:
            volumen=volumen,
            # Color:
            rgb_color=rgb_color,
            # Agarrable:
            agarrado_por=agarrado_por,
            # Destruible:
            durabilidad_max=durabilidad_max,
            # Ingrediente:
            recetas_de=recetas_de,  # Termico:
            temperatura_propia=temperatura_propia,
            tasa_transferencia=tasa_transferencia,
            radio_termico=radio_termico,
            # Erosionable:
            condiciones_erosion=condiciones_erosion,
            durabilidad_max_erosion=durabilidad_max_erosion,
            # Destruible:
            durabilidad_actual=durabilidad_actual,
            # Erosionable:
            durabilidad_actual_erosion=durabilidad_actual_erosion,
            # Sonoro:
            sonidos={
                "GOLPEAR": [
                    Sonoro.generar_timbre(
                        fundamental=lambda: 950.0 / (peso ** (1 / 3)),
                        n_armonicos=80,
                        decay=0.45,
                        inarmonicidad=0.08,
                    ),
                    Sonoro.generar_timbre(
                        fundamental=lambda: 380.0 / (peso ** (1 / 3)),
                        n_armonicos=12,
                        decay=0.60,
                        inarmonicidad=0.12,
                    ),
                ],
                "EMPUJAR": [
                    Sonoro.generar_timbre(
                        fundamental=lambda: 2000 / (peso ** (1 / 3)),
                        n_armonicos=4,
                        decay=0.6,
                        inarmonicidad=0.0,
                    )
                ],
            },
            **kwargs,
        )
