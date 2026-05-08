from Core.Entities.Comportamiento.Energetico.termico import Termico
from Core.Entities.Comportamiento.Fisico.peso import Peso
from Core.Entities.Comportamiento.Fisico.volumen import Volumen
from Core.Entities.Comportamiento.Interaccion.consumible import Consumible
from Core.Entities.Comportamiento.Interaccion.ingrediente import Ingrediente
from Core.Entities.Comportamiento.Material.combinable import Combinable
from Core.Entities.Comportamiento.Material.divisible import Divisible
from Core.Entities.Comportamiento.Material.liquido import Liquido
from Core.Entities.Comportamiento.Material.tangible import Tangible
from Core.Entities.Comportamiento.Material.transformable import Transformable
from Core.Entities.Comportamiento.Material.transparente import Transparente
from Core.Entities.Comportamiento.Salud.comestible import Comestible
from Core.Entities.Comportamiento.Salud.hidratante import Hidratante
from Core.Entities.Elementos.Simples.elemento_simple import Elemento_Simple
from Core.Entities.Comportamiento.comportamiento import Comportamiento

from Core.Entities.Elementos.Simples.Agua.diccionario_trans_agua import (
    diccionario_trans_agua,
)

comportamientos = Comportamiento.declarar_comportamientos(
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
    Termico,
)


class Agua(Elemento_Simple, comportamientos):

    cantidad_max = 1000  # (ml o cm3)

    def __init__(
        self,
        casilla: tuple[int, int],
        # Peso:
        peso: float,
    ):
        if peso < 0:
            peso = 0
        super().__init__(
            tipo=Agua,
            tamanho=1,
            casilla=casilla,
            capa=1,
            # Volumen:
            volumen=peso,
            # Peso:
            peso=peso,
            # Ingrediente:
            recetas_de=recetas_de,
            # Divisible:
            cantidad_minima_divisible=1,
            # Transformable:
            dict_transformable=diccionario_trans_agua,
            # Hidratante:
            valor_hidratacion=valor_hidratacion,
            # Combinable:
            cantidad_max_combinable=cantidad_max_combinable,
        )
