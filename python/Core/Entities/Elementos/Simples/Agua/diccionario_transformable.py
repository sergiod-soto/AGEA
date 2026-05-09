from functools import partial
from typing import Callable

from Core.Entities.Comportamiento.Fisico.empujable import Empujable
from Core.Entities.Comportamiento.Interaccion.agarrable import Agarrable
from Core.Entities.Comportamiento.Interaccion.equipable import Equipable
from Core.Entities.Comportamiento.Interaccion.golpeable import Golpeable
from Core.Entities.Comportamiento.Material.liquido import Liquido
from Core.Entities.Comportamiento.Material.solido import Solido
from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion
from Core.Entities.Elementos.Simples.Agua import Agua
from Core.Entities.Elementos.elemento import Elemento


def _CHECK_CONDICION_AGUA_HIELO(agua: Agua) -> Condicion:
    return Condicion(
        evaluar_fn=lambda: agua.temperatura_propia <= 0.0,
        eventos=["CONDICION_AGUA_HIELO"],
    )


def _FUNCION_CONDICION_AGUA_HIELO(agua: Agua) -> None:

    #
    Comportamiento.quitar(agua, Liquido)

    #   Solido
    Comportamiento.anhadir(agua, Solido)

    #   Empujable
    def _check_push(direccion): ...  # TODO: definir _check_push de Empujable de hielo

    def _push(direccion): ...  # TODO: definir _push de Empujable de hielo

    Comportamiento.anhadir(
        agua,
        Empujable,
        coste_empujar=0.0,  #    TODO: definir cuanto cuesta mover el hielo
        check_push=_check_push,
        push=_push,
    )

    #   Agarrable
    def _agarrar(por: Elemento): ...  #   TODO: definir _agarrar de Agarrable de hielo
    def _soltar(por: Elemento): ...  #   TODO: definir _soltar de Agarrable de hielo

    Comportamiento.anhadir(
        agua,
        Agarrable,
        agarrar=_agarrar,
        soltar=_soltar,
    )

    #   Golpeable
    def _golpear(por: Elemento): ...  #   TODO: definir _golpear de Golpeable de hielo

    Comportamiento.anhadir(
        agua,
        Golpeable,
        golpear=_golpear,
    )

    #   Equipable
    def _equipar(por: Elemento): ...  #   TODO: definir _equipar de Equipable de hielo
    def _desequipar(
        por: Elemento,
    ): ...  #   TODO: definir _desequipar de Equipable de hielo

    Comportamiento.anhadir(
        agua,
        Equipable,
        equipar=_equipar,
        desequipar=_desequipar,
    )


###################################################


def _CHECK_CONDICION_HIELO_AGUA(agua: Agua):
    return Condicion(
        evaluar_fn=lambda: agua.temperatura_propia > 0.0,
        eventos=["CONDICION_HIELO_AGUA"],
    )


def _FUNCION_CONDICION_HIELO_AGUA(agua: Agua):
    #
    Comportamiento.quitar(agua, Solido)
    Comportamiento.quitar(agua, Empujable, ...)
    Comportamiento.quitar(agua, Agarrable)
    Comportamiento.quitar(agua, Golpeable)
    Comportamiento.quitar(agua, Equipable)
    #
    Comportamiento.anhadir(agua, Solido)


###################################################


def _CHECK_CONDICION_VAPOR_AGUA(agua: Agua):
    Condicion(
        evaluar_fn=lambda: agua.temperatura_propia < 100.0,
        eventos=["CONDICION_VAPOR_AGUA:"],
    )


def _FUNCION_CONDICION_VAPOR_AGUA(agua: Agua):
    #
    Comportamiento.quitar(agua, Solido)
    Comportamiento.quitar(agua, Empujable, ...)
    Comportamiento.quitar(agua, Agarrable)
    Comportamiento.quitar(agua, Golpeable)
    Comportamiento.quitar(agua, Equipable)
    #
    Comportamiento.anhadir(agua, Solido)


###################################################


def _CHECK_CONDICION_AGUA_VAPOR(agua: Agua):
    return Condicion(
        evaluar_fn=lambda: agua.temperatura_propia >= 100.0,
        eventos=["CONDICION_AGUA_VAPOR"],
    )


def _FUNCION_CONDICION_AGUA_VAPOR(agua: Agua):
    #
    Comportamiento.quitar(agua, Solido)
    Comportamiento.quitar(agua, Empujable, ...)
    Comportamiento.quitar(agua, Agarrable)
    Comportamiento.quitar(agua, Golpeable)
    Comportamiento.quitar(agua, Equipable)
    #
    Comportamiento.anhadir(agua, Solido)


###################################################


def diccionario_transformaciones(agua: Agua):

    return {
        _CHECK_CONDICION_AGUA_HIELO(agua): _FUNCION_CONDICION_AGUA_HIELO(agua),
        _CHECK_CONDICION_HIELO_AGUA(agua): _FUNCION_CONDICION_HIELO_AGUA(agua),
        _CHECK_CONDICION_VAPOR_AGUA(agua): _FUNCION_CONDICION_VAPOR_AGUA(agua),
        _CHECK_CONDICION_AGUA_VAPOR(agua): _FUNCION_CONDICION_AGUA_VAPOR(agua),
    }
