# Core/Entities/Elementos/Simples/Agua/agua.py

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
from Core.Entities.Comportamiento.Salud.comestible import Comestible
from Core.Entities.Comportamiento.Salud.hidratante import Hidratante
from Core.Entities.Elementos.Simples.Agua.recetas_con import recetas_con_agua
from Core.Entities.Elementos.Simples.elemento_simple import Elemento_Simple
from Core.Entities.Comportamiento.comportamiento import Comportamiento

from Core.Entities.Elementos.Simples.Agua.diccionario_transformable import (
    diccionario_transformaciones,
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
    Comestible,
    Hidratante,
    Termico,
)


class Agua(Elemento_Simple, comportamientos):

    cantidad_max = 1000  # (ml o cm3)

    def __init__(
        self,
        id_elemento,
        casilla: tuple[int, int],
        # Peso:
        peso: float,
        rotacion=0,
        fuerza_sector_activo=False,
        fuerza_vecinos_activos=False,
        gestionado_por_hidrografia: bool = False,
        **kwargs
    ):
        if peso < 0:
            peso = 0
        self.gestionado_por_hidrografia = bool(gestionado_por_hidrografia)

        temperatura_propia = kwargs.pop("temperatura_propia", 20.0)
        tasa_transferencia_temperatura = kwargs.pop(
            "tasa_transferencia_temperatura", 0.6
        )
        radio_termico = kwargs.pop("radio_termico", 0)

        self.fuerza_sector_activo = fuerza_sector_activo
        self.fuerza_vecinos_activos = fuerza_vecinos_activos
        super().__init__(
            tipo=Agua,
            id_elemento=id_elemento,
            tamanho=1,
            casilla=casilla,
            capa=1,
            # Volumen:
            volumen=peso,
            # Peso:
            peso=peso,
            # Termico:
            temperatura_propia=temperatura_propia,
            tasa_transferencia_temperatura=tasa_transferencia_temperatura,
            radio_termico=radio_termico,
            # Ingrediente:
            recetas_de=[],
            # Divisible:
            cantidad_minima_divisible=1,
            # Liquido
            disuelto=None,
            # Transformable:
            dict_transformable=diccionario_transformaciones(),
            # Hidratante:
            valor_hidratacion=1.0,  # TODO: definir _valor_hidratacion de Hidratante de agua
            # Combinable:
            cantidad_max_combinable=1000.0,
            rotacion=rotacion,
            **kwargs
        )

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["gestionado_por_hidrografia"] = self.gestionado_por_hidrografia
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        self.gestionado_por_hidrografia = bool(
            data.get("gestionado_por_hidrografia", False)
        )
