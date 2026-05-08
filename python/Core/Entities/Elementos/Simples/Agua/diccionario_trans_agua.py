from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion
from Core.Entities.Elementos.Simples.Agua import Agua
from Core.Entities.Elementos.elemento import Elemento


def diccionario_trans_agua(agua: Agua):

    # Condiciones
    CONDICION_AGUA_HIELO = Condicion(
        evaluar_fn=lambda agua: agua.temperatura_propia <= 0.0,
        eventos=["CONDICION_AGUA_HIELO"],
    )

    CONDICION_HIELO_AGUA = Condicion(
        evaluar_fn=lambda agua: agua.temperatura_propia > 0.0,
        eventos=["CONDICION_HIELO_AGUA"],
    )

    CONDICION_AGUA_VAPOR = Condicion(
        evaluar_fn=lambda agua: agua.temperatura_propia >= 100.0,
        eventos=["CONDICION_AGUA_VAPOR"],
    )

    CONDICION_VAPOR_AGUA = Condicion(
        evaluar_fn=lambda agua: agua.temperatura_propia < 100.0,
        eventos=["CONDICION_VAPOR_AGUA:"agua],
    )

    # Acciones

    diccionario: dict[Condicion, Elemento] = {
        #
    }
