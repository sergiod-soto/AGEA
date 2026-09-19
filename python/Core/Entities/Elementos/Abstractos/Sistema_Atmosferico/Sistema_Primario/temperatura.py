# Core/Entities/Elementos/Abstractos/Sistema_Atmosferico/Sistema_Primario/temperatura.py

from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
    Sistema_Atmosferico,
)
from Core.Entities.Mundo.Bioma.bioma import Bioma

# ---- Constantes del modelo (ajustables sin tocar la lógica) ----

# Fracción de la diferencia de temperatura con cada vecino que se
# transfiere en un tick. 0 = celdas completamente aisladas entre sí,
# 1 = igualan su temperatura con ese vecino de golpe.
DIFUSION_TERMICA: float = 0.05

# Pérdida de calor hacia un ambiente de referencia, independiente de los
# vecinos (radiación de vuelta al espacio/entorno). Sin esto, un grupo
# de celdas sin fuga de calor convergería todas a la misma temperatura
# y no bajaría nunca -- esto da un "suelo" al que tender en ausencia de
# radiación entrante.
TEMPERATURA_AMBIENTE: float = 15.0
PERDIDA_AMBIENTE: float = 0.01


class Temperatura(Sistema_Atmosferico):
    def __init__(self, valor_inicial: float = 20.0, **kwargs):
        super().__init__(Temperatura, **kwargs)
        self.valor: float = valor_inicial

    def actualizar(self, bioma: Bioma, radiacion: float, vecinos: list) -> None:
        """
        Avanza la temperatura un tick. Se mueve por tres fuerzas, todas
        amortiguadas por bioma.inercia_termica (a más inercia, más lento
        cambia la celda ante cualquiera de las tres):

          1) calor_por_radiacion: la radiación entrante de este tick
             convertida a calor según bioma.tasa_conversion_radiacion_calor
             -- esto es lo que hace que un bioma pueda absorber
             radiación de forma más o menos eficiente que otro.
          2) calor_por_difusion: suma, por cada vecino, de la diferencia
             de temperatura con él, ponderada por DIFUSION_TERMICA -- el
             calor fluye del más caliente al más frío.
          3) perdida_ambiente: fuga constante hacia TEMPERATURA_AMBIENTE.

        `vecinos` son EstadoVecino del TICK ANTERIOR (ghost zone) -- ver
        Infraestructura/Gestores/Mundo/Atmosfera/sistema_atmosferico.py.

        PRECONDICIÓN no validada a propósito: `bioma` debe tener ya
        definidos tasa_conversion_radiacion_calor e inercia_termica
        (pendiente de añadir en Bioma/sus subclases). Si faltan, esto
        revienta con un AttributeError explícito -- preferible a un
        valor por defecto inventado y silencioso.
        """
        calor_por_radiacion = radiacion * bioma.tasa_conversion_radiacion_calor

        calor_por_difusion = sum(
            (vecino.temperatura - self.valor) * DIFUSION_TERMICA for vecino in vecinos
        )

        perdida_ambiente = (self.valor - TEMPERATURA_AMBIENTE) * PERDIDA_AMBIENTE

        delta_neto = (
            calor_por_radiacion + calor_por_difusion - perdida_ambiente
        ) / bioma.inercia_termica

        self.valor += delta_neto
