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
from Core.Entities.Comportamiento.Salud.comestible import Comestible
from Core.Entities.Comportamiento.Salud.hidratante import Hidratante
from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion
from Core.Entities.Elementos.Simples.Agua import Agua
from Core.Entities.Elementos.elemento import Elemento


def _CONDICION_TRANSFORMACION_AGUA_HIELO(agua: Agua) -> Condicion:
    return Condicion(
        evaluar_fn=lambda: agua.temperatura_propia <= 0.0,
        eventos=[f"temperatura_cambiada_{id(agua)}"],
    )


def _FUNCION_TRANSFORMACION_AGUA_HIELO(agua: Agua) -> None:

    #
    Comportamiento.quitar(agua, Liquido)
    Comportamiento.quitar(agua, Consumible)

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


def _CONDICION_TRANSFORMACION_HIELO_AGUA(agua: Agua):
    return Condicion(
        evaluar_fn=lambda: agua.temperatura_propia > 0.0,
        eventos=[f"temperatura_cambiada_{id(agua)}"],
    )


def _FUNCION_TRANSFORMACION_HIELO_AGUA(agua: Agua):

    #
    Comportamiento.quitar(agua, Solido)
    Comportamiento.quitar(agua, Empujable)
    Comportamiento.quitar(agua, Agarrable)
    Comportamiento.quitar(agua, Golpeable)
    Comportamiento.quitar(agua, Equipable)
    #
    #   Liquido
    Comportamiento.anhadir(agua, Liquido)

    # Consumible
    def _consumir(por: Elemento): ...  #   TODO: definir _consumir de Consumible de agua

    Comportamiento.anhadir(
        agua,
        Consumible,
        consumir=_consumir,
    )


###################################################


def _CONDICION_TRANSFORMACION_AGUA_VAPOR(agua: Agua):
    return Condicion(
        evaluar_fn=lambda: agua.temperatura_propia >= 100.0,
        eventos=[f"temperatura_cambiada_{id(agua)}"],
    )


def _FUNCION_TRANSFORMACION_AGUA_VAPOR(agua: Agua):
    #
    Comportamiento.quitar(agua, Liquido)
    Comportamiento.quitar(agua, Comestible)
    Comportamiento.quitar(agua, Peso)
    Comportamiento.quitar(agua, Tangible)
    Comportamiento.quitar(agua, Hidratante)

    #   Gaseoso
    Comportamiento.anhadir(agua, Gaseoso)


###################################################


def _CONDICION_TRANSFORMACION_VAPOR_AGUA(agua: Agua):
    Condicion(
        evaluar_fn=lambda: agua.temperatura_propia < 100.0,
        eventos=[f"temperatura_cambiada_{id(agua)}"],
    )


def _FUNCION_TRANSFORMACION_VAPOR_AGUA(agua: Agua):
    #
    Comportamiento.quitar(agua, Gaseoso)

    #   Liquido
    Comportamiento.anhadir(agua, Liquido)

    #   Comestible
    def _comer(por: Elemento): ...  # TODO: definir _comer de Comestible de agua

    Comportamiento.anhadir(
        agua,
        Comestible,
        comer=_comer,
    )

    #   Peso
    _peso = 0.0  # TODO: definir _peso de Peso de agua
    Comportamiento.anhadir(agua, Peso, peso=_peso)

    #   Tangible
    Comportamiento.anhadir(agua, Tangible)

    #   Hidratante
    _valor_hidratacion = 1  # TODO: definir _valor_hidratacion de Hidratante de agua
    Comportamiento.anhadir(agua, Hidratante, valor_hidratacion=_valor_hidratacion)


###################################################


def diccionario_transformaciones(agua: Agua):

    return {
        _CONDICION_TRANSFORMACION_AGUA_HIELO(agua): _FUNCION_TRANSFORMACION_AGUA_HIELO(
            agua
        ),
        _CONDICION_TRANSFORMACION_HIELO_AGUA(agua): _FUNCION_TRANSFORMACION_HIELO_AGUA(
            agua
        ),
        _CONDICION_TRANSFORMACION_VAPOR_AGUA(agua): _FUNCION_TRANSFORMACION_VAPOR_AGUA(
            agua
        ),
        _CONDICION_TRANSFORMACION_AGUA_VAPOR(agua): _FUNCION_TRANSFORMACION_AGUA_VAPOR(
            agua
        ),
    }
