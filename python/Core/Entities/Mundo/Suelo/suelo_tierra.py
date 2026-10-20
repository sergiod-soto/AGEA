# Core/Entities/Mundo/Suelo/suelo_tierra.py
from Core.Entities.Comportamiento.Material.registro_transformaciones import registrar

from Core.Entities.Comportamiento.Material.transformable import Transformable
from Core.Entities.Comportamiento.Terreno.terroso import Terroso
from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Entities.Elementos.Abstractos.Condiciones.Condiciones_Atmosfericas.condicion_umbral_humedad import (
    CondicionUmbralHumedad,
)
from Core.Entities.Elementos.Abstractos.Condiciones.Condiciones_Fisicas.condicion_vecino_cercano import (
    CondicionVecinoCercano,
)
from Core.Entities.Elementos.Abstractos.Condiciones.Condiciones_Logicas.condicion_and import (
    CondicionAnd,
)
from Core.Entities.Mundo.Suelo.suelo import Suelo

RADIO_CESPED_CERCANO: int = 3
UMBRAL_HUMEDAD_MIN: float = 5.0
UMBRAL_HUMEDAD_MAX: float = 10.0

comportamientos = Comportamiento.declarar_comportamientos(
    Transformable,
)


@registrar("suelo_tierra_convertir_cesped")
def _convertir_a_cesped(suelo, ctx) -> None:
    from Core.Entities.Mundo.Suelo.suelo_cesped import Suelo_Cesped

    ctx.eliminar_elemento(suelo.id_elemento, suelo.casilla)
    ctx.guardar_elemento(
        pos=suelo.casilla,
        elemento=Suelo_Cesped(casilla=suelo.casilla, id_elemento=suelo.id_elemento),
    )


class Suelo_Tierra(Suelo, Terroso, comportamientos):
    def __init__(self, casilla, id_elemento, **kwargs):
        super().__init__(
            casilla=casilla,
            id_elemento=id_elemento,
            tipo=Suelo_Tierra,
            tasa_conversion_radiacion_calor=80,
            inercia_termica=3e5,
            dict_transformable={
                "suelo_tierra_convertir_cesped": CondicionAnd(
                    [
                        CondicionUmbralHumedad(
                            umbral=UMBRAL_HUMEDAD_MIN, por_debajo=False
                        ),
                        CondicionUmbralHumedad(
                            umbral=UMBRAL_HUMEDAD_MAX, por_debajo=True
                        ),
                        CondicionVecinoCercano(
                            tipo_buscado="Suelo_Cesped", radio=RADIO_CESPED_CERCANO
                        ),
                    ]
                )
            },
            **kwargs,
        )

    def tick_elemento(self, ctx): ...
