from Core.Entities.Elementos.Abstractos.Condiciones.Condiciones_Atmosfericas.condicion_umbral_humedad import (
    CondicionUmbralHumedad,
)
from Core.Entities.Elementos.Abstractos.Condiciones.Condiciones_Fisicas.condicion_vecino_cercano import (
    CondicionVecinoCercano,
)
from Core.Entities.Elementos.Abstractos.Condiciones.Condiciones_Logicas.condicion_and import (
    CondicionAnd,
)
from Core.Entities.Mundo.Suelo.suelo_tierra import (
    RADIO_CESPED_CERCANO,
    UMBRAL_HUMEDAD_MAX,
    UMBRAL_HUMEDAD_MIN,
)

dict_transformacion = {
    "suelo_tierra_convertir_cesped": CondicionAnd(
        [
            CondicionUmbralHumedad(umbral=UMBRAL_HUMEDAD_MIN, por_debajo=False),
            CondicionUmbralHumedad(umbral=UMBRAL_HUMEDAD_MAX, por_debajo=True),
            CondicionVecinoCercano(
                tipo_buscado="Suelo_Cesped", radio=RADIO_CESPED_CERCANO
            ),
        ]
    )
}
