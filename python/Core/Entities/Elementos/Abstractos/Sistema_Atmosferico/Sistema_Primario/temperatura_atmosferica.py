# Core/Entities/Elementos/Abstractos/Sistema_Atmosferico/Sistema_Primario/temperatura_atmosferica.py

"""
Temperatura de una celda de atmósfera, en unidades del SISTEMA INTERNACIONAL.

Cada celda lleva DOS temperaturas, ambas en K:
  - valor ........ temperatura del AIRE. Es la que leen presión, viento,
                   humedad, vecinos, proto y snapshots.
  - valor_suelo .. temperatura del SUELO (media de las casillas de la celda).

Unidades:
  - radiacion .......................... W/m². Es lo que llega del sol: no se
                                         "emite" en este modelo.
  - inercia_termica .................... J/(m²·K) del SUELO de la celda (media
                                         de sus casillas). El aire se cuenta
                                         aparte con C_AIRE.
  - tasa_conversion_radiacion_calor .... 0-100: 0 = espejo, 100 = cuerpo negro
                                         (porcentaje de radiación que el suelo
                                         convierte en calor).
  - tiempo ............................. s. Cada tick avanza la simulación
                                         dt = SEGUNDOS_SIMULADOS_TICK segundos.

Modelo (balance de potencia por m² de celda):

    inercia · dTs/dt = absorbido - K·(Ts - Ta)
    C_AIRE  · dTa/dt = K·(Ts - Ta) - emitido + C_AIRE·difusion + adveccion

  absorbido = radiacion · (tasa / 100)         el suelo convierte sol en calor
  K·(Ts-Ta) = calor del suelo al aire          el suelo calienta el aire
  emitido   = ε · σ · Ta⁴                      el AIRE emite al espacio
  difusion  = Σ_vecinos (D/L²)·(Ta_v - Ta)     mezcla lateral (solo aire)

Por qué emite el aire y no el suelo: en la Tierra, lo que escapa al espacio lo
emite sobre todo la atmósfera, no la superficie. La estabilidad sale de que la
pérdida crece con Ta⁴: no hay techo artificial de temperatura. Sin radiación,
la celda se enfría hacia 0 K (cada vez más despacio).
"""

from Config.parametros_simulacion import (
    C_AIRE,
    SEGUNDOS_SIMULADOS_TICK,
    TAMANHO_CELDA_ATMOSFERICA,
)
from Config.settings import ID_TEMPERATURA_ATMOSFERICA
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
    Sistema_Atmosferico,
)
from Core.Fisica.termodinamica import celsius_a_kelvin

# ---- Constantes físicas ----

# Constante de Stefan-Boltzmann, W/(m²·K⁴).
CONSTANTE_STEFAN_BOLTZMANN: float = 5.670374419e-8



# ---- Constantes del modelo (ajustables sin tocar la lógica; SIN CALIBRAR) ----

# Fracción de la potencia emitida por el aire que de verdad escapa al espacio
# (efecto invernadero). Con 0.52, ~24-27 °C de media en el ecuador. A futuro:
# ligarlo a la humedad absoluta.
EMISIVIDAD_EFECTIVA: float = 0.52


# Intercambio de calor suelo <-> aire, W/(m²·K).
COEFICIENTE_INTERCAMBIO_SUELO_AIRE: float = 25.0

# Difusividad térmica del aire, m²/s. Mismo criterio que humedad y presión.
DIFUSIVIDAD_TERMICA: float = 5.0

# Fracción de la diferencia con CADA vecino que se iguala por segundo, 1/s
# (D/L²): al cambiar el tamaño de celda, la física cambia de forma coherente.
_COEFICIENTE_DIFUSION: float = DIFUSIVIDAD_TERMICA / TAMANHO_CELDA_ATMOSFERICA**2


class TemperaturaAtmosferica(Sistema_Atmosferico):
    def __init__(
        self,
        valor_inicial: float = celsius_a_kelvin(15.0),
        valor_suelo_inicial: float | None = None,
        **kwargs,
    ):
        super().__init__(
            TemperaturaAtmosferica,
            ID_TEMPERATURA_ATMOSFERICA,
            **kwargs,
        )
        # K. Temperatura del AIRE: es la que todo lo demás lee como `.valor`.
        self.valor: float = valor_inicial
        # K. Temperatura del SUELO. Arranca igual que el aire si no se indica.
        self.valor_suelo: float = (
            valor_inicial if valor_suelo_inicial is None else valor_suelo_inicial
        )

    def actualizar(
        self,
        tasa_conversion_radiacion_calor: float,
        inercia_termica: float,
        radiacion: float,
        vecinos: list,
        velocidad: tuple[float, float],
        bloqueado: bool,
    ) -> None:
        """
        Avanza las dos temperaturas un tick (dt = SEGUNDOS_SIMULADOS_TICK s).

        `tasa_conversion_radiacion_calor` e `inercia_termica` son las MEDIAS
        ya resueltas por Celda_Atmosfera. `vecinos` son EstadoVecino del TICK
        ANTERIOR (ghost zone), con `temperatura` = temperatura del AIRE (K).

        PRECONDICIONES (ValueError, mejor que un valor silencioso): tasa en
        [0, 100]; inercia_termica > 0 (sin Suelo registrado no hay media
        válida); ambas temperaturas > 0 K.

        ESTABILIDAD: paso explícito (Euler). Hace falta que cada una sea < 1:
            suelo:  dt · K / inercia_termica
            aire:   dt · (K + 4·ε·σ·Ta³) / C_AIRE
            mezcla: dt · (D/L²) · n_vecinos        (n = 4: 0.05·1·4 = 0.2)
        Con dt = 1 s y los valores actuales todas quedan muy por debajo de 1.
        Si se sube dt o se baja TAMANHO_CELDA_ATMOSFERICA, hay que revisarlo.
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
        if self.valor <= 0 or self.valor_suelo <= 0:
            raise ValueError(
                f"Temperatura <= 0 K (aire {self.valor}, suelo "
                f"{self.valor_suelo}): simulación inestable."
            )

        dt = SEGUNDOS_SIMULADOS_TICK

        # Todos los flujos se calculan con los valores del INICIO del tick y
        # solo después se actualizan las dos temperaturas: así el calor que
        # sale del suelo es exactamente el que entra en el aire.

        # W/m²: radiación solar que el suelo convierte en calor.
        potencia_absorbida = radiacion * (tasa_conversion_radiacion_calor / 100.0)

        # W/m²: calor del suelo al aire (negativo si el aire está más caliente).
        flujo_suelo_aire = COEFICIENTE_INTERCAMBIO_SUELO_AIRE * (
            self.valor_suelo - self.valor
        )

        # W/m²: Stefan-Boltzmann. El AIRE emite al espacio; es lo que frena el
        # calentamiento sin ningún tope artificial.
        potencia_emitida = (
            EMISIVIDAD_EFECTIVA * CONSTANTE_STEFAN_BOLTZMANN * self.valor**4
        )

        # K/s: mezcla lateral del aire con los vecinos.
        ritmo_difusion = sum(
            _COEFICIENTE_DIFUSION * (vecino.temperatura - self.valor)
            for vecino in vecinos
        )

        # K: aire que entra/sale con el viento por cada cara cardinal. Ya
        # incluye dt. Se calcula con el valor del inicio del tick.
        adveccion = sum(
            self.delta_advectivo(
                self.valor,
                vecino.temperatura,
                velocidad,
                (vecino.viento_x, vecino.viento_y),
                vecino.direccion,
                bloqueado or vecino.bloqueo_total_viento,
            )
            for vecino in vecinos
        )

        # Las dos temperaturas se actualizan UNA vez, con flujos del inicio del
        # tick: el calor que sale del suelo es exactamente el que entra al aire.
        # J/m² = W/m² · s;  K = (J/m²) / (J/(m²·K)).
        self.valor_suelo += (
            (potencia_absorbida - flujo_suelo_aire) * dt / inercia_termica
        )
        self.valor += (
            (flujo_suelo_aire - potencia_emitida) / C_AIRE + ritmo_difusion
        ) * dt + adveccion
