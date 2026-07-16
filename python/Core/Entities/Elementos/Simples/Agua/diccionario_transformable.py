# Core/Entities/Elementos/Simples/Agua/diccionario_transformaciones.py

# `from __future__ import annotations` pospone la evaluación de TODAS las
# anotaciones de tipo (se guardan como string, no se resuelven en tiempo de
# import) — PEP 563. Combinado con el bloque `if TYPE_CHECKING`, esto nos
# permite anotar `agua: Agua` sin necesitar importar la clase Agua en
# tiempo de ejecución, rompiendo el ciclo agua.py -> este fichero -> agua.py
# (aquí Agua nunca se usa como valor real, solo como pista de tipo).
from __future__ import annotations

import functools
from typing import TYPE_CHECKING

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
from Core.Entities.Elementos.elemento import Elemento

# Import SOLO visible para el type checker (mypy/pyright), nunca se ejecuta
# en tiempo real — así Agua no aparece en sys.modules como dependencia de
# este fichero y el ciclo desaparece.
if TYPE_CHECKING:
    from Core.Entities.Elementos.Simples.Agua.agua import Agua


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


def _CONDICION_TRANSFORMACION_HIELO_AGUA(agua: Agua) -> Condicion:
    return Condicion(
        evaluar_fn=lambda: agua.temperatura_propia > 0.0,
        eventos=[f"temperatura_cambiada_{id(agua)}"],
    )


def _FUNCION_TRANSFORMACION_HIELO_AGUA(agua: Agua) -> None:

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


def _CONDICION_TRANSFORMACION_AGUA_VAPOR(agua: Agua) -> Condicion:
    return Condicion(
        evaluar_fn=lambda: agua.temperatura_propia >= 100.0,
        eventos=[f"temperatura_cambiada_{id(agua)}"],
    )


def _FUNCION_TRANSFORMACION_AGUA_VAPOR(agua: Agua) -> None:
    #
    Comportamiento.quitar(agua, Liquido)
    Comportamiento.quitar(agua, Comestible)
    Comportamiento.quitar(agua, Peso)
    Comportamiento.quitar(agua, Tangible)
    Comportamiento.quitar(agua, Hidratante)

    #   Gaseoso
    Comportamiento.anhadir(agua, Gaseoso)


###################################################


def _CONDICION_TRANSFORMACION_VAPOR_AGUA(agua: Agua) -> Condicion:
    # FIX: faltaba el `return` — sin él, esta función siempre devolvía
    # None y la transformación vapor->agua nunca podía dispararse (la
    # clave del diccionario habría sido `None` en vez de una Condicion).
    return Condicion(
        evaluar_fn=lambda: agua.temperatura_propia < 100.0,
        eventos=[f"temperatura_cambiada_{id(agua)}"],
    )


def _FUNCION_TRANSFORMACION_VAPOR_AGUA(agua: Agua) -> None:
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


def diccionario_transformaciones(agua: Agua) -> dict[Condicion, "functools.partial"]:
    """
    Construye el mapa Condicion -> callable que Transformable usa para
    saber, ante cada evento de cambio de temperatura, si debe disparar
    una transformación y cuál.

    FIX IMPORTANTE: antes se escribía `_FUNCION_TRANSFORMACION_X(agua)`
    (CON paréntesis) como valor del diccionario. Eso NO registra la
    función para más tarde: la EJECUTA en el momento de construir este
    diccionario, es decir, dentro de Agua.__init__ — con lo que un Agua
    recién creado sufría las 4 transformaciones (hielo, deshielo, vapor,
    condensación) de golpe, sin que ninguna condición se hubiera evaluado
    todavía.

    Ahora se usa `functools.partial(funcion, agua)`: crea un callable
    "congelado" con `agua` ya inyectado como argumento, pero SIN
    ejecutarlo — queda listo para que Transformable lo llame él mismo
    cuando compruebe que la condición correspondiente se cumple.
    """
    return {
        _CONDICION_TRANSFORMACION_AGUA_HIELO(agua): functools.partial(
            _FUNCION_TRANSFORMACION_AGUA_HIELO, agua
        ),
        _CONDICION_TRANSFORMACION_HIELO_AGUA(agua): functools.partial(
            _FUNCION_TRANSFORMACION_HIELO_AGUA, agua
        ),
        _CONDICION_TRANSFORMACION_VAPOR_AGUA(agua): functools.partial(
            _FUNCION_TRANSFORMACION_VAPOR_AGUA, agua
        ),
        _CONDICION_TRANSFORMACION_AGUA_VAPOR(agua): functools.partial(
            _FUNCION_TRANSFORMACION_AGUA_VAPOR, agua
        ),
    }
