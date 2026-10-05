# Core/Entities/Elementos/Abstractos/Sistema_Atmosferico/Sistema_Primario/temperatura_atmosferica.py

"""
Temperatura de una celda de atmósfera, en unidades del SISTEMA INTERNACIONAL.

Unidades (todas SI salvo la tasa de conversión):
  - temperatura ........................ K (kelvin). SIEMPRE kelvin dentro del
                                         sistema; kelvin_a_celsius() solo para
                                         mostrar o para fórmulas que pidan °C
                                         (p. ej. Magnus en humedad_relativa).
  - radiacion .......................... W/m².
  - inercia_termica .................... J/(m²·K) de la CELDA COMPLETA (aire +
                                         suelo), ya promediada por
                                         Celda_Atmosfera.
  - tasa_conversion_radiacion_calor .... 0-100 adimensional: 0 = espejo,
                                         100 = cuerpo negro (absorptividad %).
  - tiempo ............................. s. Cada tick avanza la simulación
                                         dt = SEGUNDOS_SIMULADOS_TICK segundos.

Modelo: balance de potencia por m² de celda.

    inercia * dT/dt = absorbido + difusion - emitido

  absorbido = radiacion * (tasa / 100)
  emitido   = EMISIVIDAD_EFECTIVA * sigma * T^4          (Stefan-Boltzmann)
  difusion  = suma sobre vecinos de COEFICIENTE_DIFUSION_TERMICA * (T_v - T)

No hay suelo ni techo artificial de temperatura: la estabilidad sale de que la
pérdida crece con T^4. Sin radiación, una celda se enfría hacia 0 K (cada vez
más despacio).
"""

from Config.parametros_simulacion import (
    SEGUNDOS_SIMULADOS_TICK,
    TAMANHO_CELDA_ATMOSFERICA,
)
from Config.settings import ID_TEMPERATURA_ATMOSFERICA
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
    Sistema_Atmosferico,
)

# ---- Constantes físicas ----

# Constante de Stefan-Boltzmann, W/(m²·K⁴).
CONSTANTE_STEFAN_BOLTZMANN: float = 5.670374419e-8

# Diferencia entre las escalas Celsius y kelvin.
_KELVIN_EN_CERO_CELSIUS: float = 273.15

# ---- Constantes del modelo (ajustables sin tocar la lógica) ----

# Fracción de la potencia emitida que de verdad escapa al espacio (efecto
# invernadero). SIN CALIBRAR de forma fina: 0.52 da ~27 °C de media en el
# ecuador para roca (tasa 75) con 1000 W/m² de pico. A futuro: ligarlo a la
# humedad absoluta.
EMISIVIDAD_EFECTIVA: float = 0.52

# Calor que fluye hacia CADA vecino por kelvin de diferencia, en W/K, para la
# celda completa. SIN CALIBRAR. Con celdas de 10 m equivale al 1.0 W/(m²·K)
# que había antes.
CONDUCTANCIA_LATERAL_EFECTIVA: float = 100.0

# La inercia está por m² de celda, así que la conductancia también se pasa a
# W/(m²·K) dividiendo por el área de la celda (L²). Por eso, al cambiar el
# tamaño de celda, el intercambio lateral se reescala solo.
COEFICIENTE_DIFUSION_TERMICA: float = (
    CONDUCTANCIA_LATERAL_EFECTIVA / TAMANHO_CELDA_ATMOSFERICA**2
)

# Inercia térmica del AIRE de la celda, J/(m²·K). El aire es la propia celda
# atmosférica (no el suelo), así que su inercia se declara aquí y la suma
# Celda_Atmosfera a la media de inercias de sus Suelo. 1e6 equivale a unos
# 830 m de columna de aire (rho*cp ~ 1200 J/(m³·K)): la capa que responde al
# ciclo diario. SIN CALIBRAR.
INERCIA_TERMICA_AIRE: float = 1.0e6


def celsius_a_kelvin(celsius: float) -> float:
    """°C -> K. Para fijar valores iniciales legibles (p. ej. 15 °C)."""
    return celsius + _KELVIN_EN_CERO_CELSIUS


def kelvin_a_celsius(kelvin: float) -> float:
    """K -> °C. Solo para mostrar o para fórmulas que trabajen en °C."""
    return kelvin - _KELVIN_EN_CERO_CELSIUS


class TemperaturaAtmosferica(Sistema_Atmosferico):
    def __init__(self, valor_inicial: float = celsius_a_kelvin(15.0), **kwargs):
        super().__init__(
            TemperaturaAtmosferica,
            ID_TEMPERATURA_ATMOSFERICA,
            **kwargs,
        )
        # Kelvin. Todo lo que lea .valor (presión, viento, proto, snapshots)
        # lo recibe en kelvin.
        self.valor: float = valor_inicial

    def actualizar(
        self,
        tasa_conversion_radiacion_calor: float,
        inercia_termica: float,
        radiacion: float,
        vecinos: list,
    ) -> None:
        """
        Avanza la temperatura un tick (dt = SEGUNDOS_SIMULADOS_TICK segundos).

        `tasa_conversion_radiacion_calor` e `inercia_termica` son las MEDIAS
        ya resueltas por Celda_Atmosfera. `vecinos` son EstadoVecino del TICK
        ANTERIOR (ghost zone), con `temperatura` en kelvin.

        PRECONDICIONES (fallan con ValueError, mejor que un valor silencioso):
        tasa en [0, 100]; inercia_termica > 0 (sin Suelo registrado no hay
        media válida); temperatura propia > 0 K.

        ESTABILIDAD: paso explícito (Euler). Estable mientras
            inercia_termica > dt * (4*EMISIVIDAD_EFECTIVA*sigma*T^3
                                    + n_vecinos*COEFICIENTE_DIFUSION_TERMICA)
        unos 10 J/(m²·K) con dt = 1 s; todos los suelos reales están muy por
        encima. Si se sube dt (o se baja TAMANHO_CELDA_ATMOSFERICA) hay que
        revisarlo.
        """
        if not 0.0 <= tasa_conversion_radiacion_calor <= 100.0:
            raise ValueError(
                "tasa_conversion_radiacion_calor debe estar en [0, 100] "
                f"(recibido {tasa_conversion_radiacion_calor})."
            )
        if inercia_termica <= 0:
            raise ValueError(
                f"inercia_termica debe ser > 0 (recibido {inercia_termica}); "
                "¿celda de atmósfera sin Suelo registrado?"
            )
        if self.valor <= 0:
            raise ValueError(
                f"Temperatura <= 0 K ({self.valor}): simulación inestable."
            )

        # Segundos que avanza la simulación en este tick.
        dt = SEGUNDOS_SIMULADOS_TICK

        # W/m²: la parte de la radiación que el suelo convierte en calor.
        potencia_absorbida = radiacion * (tasa_conversion_radiacion_calor / 100.0)

        # W/m²: Stefan-Boltzmann. Es lo que frena el calentamiento sin
        # necesidad de ningún tope artificial.
        potencia_emitida = (
            EMISIVIDAD_EFECTIVA * CONSTANTE_STEFAN_BOLTZMANN * self.valor**4
        )

        # W/m²: el calor fluye del vecino más caliente al más frío.
        potencia_difusion = sum(
            COEFICIENTE_DIFUSION_TERMICA * (vecino.temperatura - self.valor)
            for vecino in vecinos
        )

        potencia_neta = potencia_absorbida + potencia_difusion - potencia_emitida

        # J/m² = W/m² * s;  K = (J/m²) / (J/(m²·K)).
        self.valor += potencia_neta * dt / inercia_termica
