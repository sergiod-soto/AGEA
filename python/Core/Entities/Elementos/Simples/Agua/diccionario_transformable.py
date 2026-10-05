# Core/Entities/Elementos/Simples/Agua/diccionario_transformaciones.py
from Core.Entities.Comportamiento.Fisico.empujable import Empujable
from Core.Entities.Comportamiento.Fisico.peso import Peso
from Core.Entities.Comportamiento.Interaccion.agarrable import Agarrable
from Core.Entities.Comportamiento.Interaccion.consumible import Consumible
from Core.Entities.Comportamiento.Interaccion.equipable import Equipable
from Core.Entities.Comportamiento.Interaccion.golpeable import Golpeable
from Core.Entities.Comportamiento.Material.gaseoso import Gaseoso
from Core.Entities.Comportamiento.Material.liquido import Liquido
from Core.Entities.Comportamiento.Material.solido import Solido
from Core.Entities.Comportamiento.Material.tangible import Tangible
from Core.Entities.Comportamiento.Material.registro_transformaciones import registrar
from Core.Entities.Comportamiento.Salud.comestible import Comestible
from Core.Entities.Comportamiento.Salud.hidratante import Hidratante
from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Entities.Elementos.Abstractos.Condiciones.Condiciones_Fisicas.condicion_temperatura import (
    CondicionTemperatura,
)
from Core.Entities.Elementos.elemento import Elemento


@registrar("agua_a_hielo")
def _transformacion_agua_hielo(agua, ctx) -> None:
    Comportamiento.quitar(agua, Liquido)
    Comportamiento.quitar(agua, Consumible)

    Comportamiento.anhadir(agua, Solido)

    def _check_push(direccion): ...  # TODO
    def _push(direccion): ...  # TODO

    Comportamiento.anhadir(
        agua, Empujable, coste_empujar=0.0, check_push=_check_push, push=_push
    )

    def _agarrar(por: Elemento): ...  # TODO
    def _soltar(por: Elemento): ...  # TODO

    Comportamiento.anhadir(agua, Agarrable, agarrar=_agarrar, soltar=_soltar)

    def _golpear(por: Elemento): ...  # TODO

    Comportamiento.anhadir(agua, Golpeable, golpear=_golpear)

    def _equipar(por: Elemento): ...  # TODO
    def _desequipar(por: Elemento): ...  # TODO

    Comportamiento.anhadir(agua, Equipable, equipar=_equipar, desequipar=_desequipar)


@registrar("hielo_a_agua")
def _transformacion_hielo_agua(agua, ctx) -> None:
    Comportamiento.quitar(agua, Solido)
    Comportamiento.quitar(agua, Empujable)
    Comportamiento.quitar(agua, Agarrable)
    Comportamiento.quitar(agua, Golpeable)
    Comportamiento.quitar(agua, Equipable)

    Comportamiento.anhadir(agua, Liquido)

    def _consumir(por: Elemento): ...  # TODO

    Comportamiento.anhadir(agua, Consumible, consumir=_consumir)


@registrar("agua_a_vapor")
def _transformacion_agua_vapor(agua, ctx) -> None:
    Comportamiento.quitar(agua, Liquido)
    Comportamiento.quitar(agua, Comestible)
    Comportamiento.quitar(agua, Peso)
    Comportamiento.quitar(agua, Tangible)
    Comportamiento.quitar(agua, Hidratante)

    Comportamiento.anhadir(agua, Gaseoso)


@registrar("vapor_a_agua")
def _transformacion_vapor_agua(agua, ctx) -> None:
    Comportamiento.quitar(agua, Gaseoso)

    Comportamiento.anhadir(agua, Liquido)

    def _comer(por: Elemento): ...  # TODO

    Comportamiento.anhadir(agua, Comestible, comer=_comer)

    _peso = 0.0  # TODO
    Comportamiento.anhadir(agua, Peso, peso=_peso)

    Comportamiento.anhadir(agua, Tangible)

    _valor_hidratacion = 1  # TODO
    Comportamiento.anhadir(agua, Hidratante, valor_hidratacion=_valor_hidratacion)


def diccionario_transformaciones() -> dict:
    return {
        "agua_a_hielo": CondicionTemperatura(umbral=0.0, por_debajo=True),
        "hielo_a_agua": CondicionTemperatura(umbral=0.0, por_debajo=False),
        "vapor_a_agua": CondicionTemperatura(umbral=100.0, por_debajo=True),
    }
