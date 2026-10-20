# Core/Entities/Mundo/Suelo/suelo_barro.py


from Core.Entities.Comportamiento.Material.registro_transformaciones import registrar

from Core.Entities.Comportamiento.Material.transformable import Transformable
from Core.Entities.Comportamiento.Terreno.embarrado import Embarrado
from Core.Entities.Elementos.Abstractos.Condiciones.Condiciones_Atmosfericas.condicion_umbral_humedad import (
    CondicionUmbralHumedad,
)
from Core.Entities.Elementos.Abstractos.Condiciones.Condiciones_Temporales.condicion_tick_objetivo import (
    CondicionTickObjetivo,
)
from Core.Entities.Mundo.Suelo.suelo import Suelo
from Core.Entities.Comportamiento.comportamiento import Comportamiento

comportamientos = Comportamiento.declarar_comportamientos(
    Transformable,
)

# Cuántos ticks seguidos por debajo del umbral hacen falta para que el
# barro se considere seco -- valor de partida, sin calibrar.
TICKS_SECADO_BARRO: int = 5000

UMBRAL_HUMEDAD_SECADO: float = 10.0


@registrar("suelo_barro_entra_en_franja_secado")
def _entra_en_franja_secado(suelo, ctx) -> None:
    """
    Se dispara al cruzar humedad < 10 % por primera vez. Sustituye la condición
    de vigilancia por el par cuenta/salida (se reemplaza el dict entero; es
    seguro porque Transformable.tick itera sobre una copia):
    - si la humedad vuelve a subir antes de cumplirse el tiempo, se vuelve a
      vigilar (_sale_de_franja_secado);
    - si se cumplen los ticks antes, se transforma de verdad (_secar_barro).
    """
    suelo.dict_transformable = {
        "suelo_barro_secar": CondicionTickObjetivo(
            tick_objetivo=ctx.tick_id + TICKS_SECADO_BARRO
        ),
        "suelo_barro_sale_de_franja_secado": CondicionUmbralHumedad(
            umbral=UMBRAL_HUMEDAD_SECADO, por_debajo=False
        ),
    }


@registrar("suelo_barro_sale_de_franja_secado")
def _sale_de_franja_secado(suelo, ctx) -> None:
    """Humedad volvió a subir antes de completar la cuenta: se
    eliminan cuenta y salida, y se restaura la vigilancia original."""
    suelo.dict_transformable = {
        "suelo_barro_entra_en_franja_secado": CondicionUmbralHumedad(
            umbral=UMBRAL_HUMEDAD_SECADO, por_debajo=True
        )
    }


@registrar("suelo_barro_secar")
def _secar_barro(suelo, ctx) -> None:
    """
    Barro -> tierra, sustitución en su sitio: se elimina este suelo y se crea
    una Tierra con el MISMO id (Logica sustituye el objeto bajo ese id; ver
    actualizar_celda). La baja va SIEMPRE antes del alta: libera el slot y la
    caché de resistencia al viento.
    """
    from Core.Entities.Mundo.Suelo.suelo_tierra import Suelo_Tierra

    ctx.eliminar_elemento(suelo.id_elemento, suelo.casilla)
    ctx.guardar_elemento(
        pos=suelo.casilla,
        elemento=Suelo_Tierra(casilla=suelo.casilla, id_elemento=suelo.id_elemento),
    )


class Suelo_Barro(Suelo, Embarrado, comportamientos):
    def __init__(self, casilla, id_elemento, **kwargs):
        super().__init__(
            casilla=casilla,
            id_elemento=id_elemento,
            tipo=Suelo_Barro,
            tasa_conversion_radiacion_calor=80,
            inercia_termica=5e5,
            dict_transformable={
                "suelo_barro_entra_en_franja_secado": CondicionUmbralHumedad(
                    umbral=UMBRAL_HUMEDAD_SECADO, por_debajo=True
                )
            },
            **kwargs,
        )

    def tick_elemento(self, ctx): ...
