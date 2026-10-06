# Core/Entities/Mundo/Suelo/suelo_barro.py


from Core.Entities.Comportamiento.Material.registro_transformaciones import registrar

from Core.Entities.Elementos.Abstractos.Condiciones.Condiciones_Atmosfericas.condicion_umbral_humedad import (
    CondicionUmbralHumedad,
)
from Core.Entities.Elementos.Abstractos.Condiciones.Condiciones_Temporales.condicion_tick_objetivo import (
    CondicionTickObjetivo,
)
from Core.Entities.Mundo.Suelo.suelo import Suelo

# Cuántos ticks seguidos por debajo del umbral hacen falta para que el
# barro se considere seco -- valor de partida, sin calibrar.
TICKS_SECADO_BARRO: int = 5000

UMBRAL_HUMEDAD_SECADO: float = 10.0


@registrar("suelo_barro_entra_en_franja_secado")
def _entra_en_franja_secado(suelo, ctx) -> None:
    """
    Se dispara al cruzar humedad < 10% por primera vez. Sustituye la
    condición de vigilancia (esta misma) por el par cuenta/salida:
    - si la humedad vuelve a subir antes de cumplirse el tiempo, se
      revierte a vigilar de nuevo (_sale_de_franja_secado).
    - si se cumplen los X ticks antes de que suba, se transforma de
      verdad (_secar_barro).
    Como Transformable.tick() itera sobre list(...) de una copia, mutar
    dict_transformable aquí dentro es seguro.
    """
    condicion_entrada = next(
        c
        for c in suelo.dict_transformable
        if suelo.dict_transformable[c] == "suelo_barro_entra_en_franja_secado"
    )
    del suelo.dict_transformable[condicion_entrada]

    tick_objetivo = ctx.tick_id + TICKS_SECADO_BARRO
    suelo.dict_transformable[CondicionTickObjetivo(tick_objetivo=tick_objetivo)] = (
        "suelo_barro_secar"
    )
    suelo.dict_transformable[
        CondicionUmbralHumedad(umbral=UMBRAL_HUMEDAD_SECADO, por_debajo=False)
    ] = "suelo_barro_sale_de_franja_secado"


@registrar("suelo_barro_sale_de_franja_secado")
def _sale_de_franja_secado(suelo, ctx) -> None:
    """Humedad volvió a subir antes de completar la cuenta: se
    eliminan cuenta y salida, y se restaura la vigilancia original."""
    suelo.dict_transformable = {
        CondicionUmbralHumedad(
            umbral=UMBRAL_HUMEDAD_SECADO, por_debajo=True
        ): "suelo_barro_entra_en_franja_secado"
    }


@registrar("suelo_barro_secar")
def _secar_barro(suelo, ctx) -> None:
    """
    Transformación real: barro -> tierra. Sustitución discreta (ruta
    (a) acordada) -- se elimina este Suelo_Barro y se crea un
    Suelo_Tierra en su lugar, vía TickContext.
    """
    from Core.Entities.Mundo.Suelo.suelo_tierra import Suelo_Tierra

    ctx.eliminar_elemento(suelo.id_elemento, suelo.casilla)
    ctx.guardar_elemento(
        pos=suelo.casilla,
        tipo_slot="suelo",
        elemento=Suelo_Tierra(
            casilla=suelo.casilla,
            id_elemento=None,  # lo asigna Logica_Mundo al resolver la mutación
            tasa_conversion_radiacion_calor=80,
            inercia_termica=1.5e6,
        ),
    )


class Suelo_Barro(Suelo):
    def __init__(self, casilla, id_elemento, **kwargs):
        super().__init__(
            casilla=casilla,
            id_elemento=id_elemento,
            tipo=Suelo_Barro,
            tasa_conversion_radiacion_calor=80,
            inercia_termica=5e5,
            dict_transformable={
                CondicionUmbralHumedad(
                    umbral=UMBRAL_HUMEDAD_SECADO, por_debajo=True
                ): "suelo_barro_entra_en_franja_secado"
            },
            **kwargs,
        )
