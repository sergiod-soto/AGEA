# Config/validacion_simulacion.py
"""
Comprobación de estabilidad numérica de la atmósfera, al arrancar.

Esquemas explícitos (Euler): la fracción total del valor de una celda que
puede salir en UN tick debe ser <= 1, o la celda puede quedar negativa.
  - Difusión: (D/L²)·dt·n_vecinos.
  - Advección (temperatura, humedad y nube): n_vecinos·FRACCION_MAXIMA_ADVECCION,
    el peor caso (viento saliendo por las 4 caras). Ese tope lo impone el
    propio cálculo (Sistema_Atmosferico.delta_advectivo); aquí se comprueba
    que, sumado a la difusión, no pasa de 1.

Vive aparte de parametros_simulacion porque importa de los módulos de las
magnitudes, que a su vez importan parametros_simulacion (sería circular).
"""

from Config.parametros_simulacion import (
    SEGUNDOS_SIMULADOS_TICK,
    TAMANHO_CELDA_ATMOSFERICA,
    TAU_LLUVIA,
)

# Vecinos cardinales por celda (los mismos que Sector._DIRECCIONES_ATMOSFERA).
_N_VECINOS = 4
# Tolerancia para el redondeo de coma flotante (0.8 + 0.2 puede dar 1.0000000000000002).
_TOLERANCIA = 1e-9


def validar_estabilidad() -> None:
    """ValueError con el detalle de TODOS los incumplimientos."""
    # Imports dentro de la función para evitar ciclos.
    from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
        FRACCION_MAXIMA_ADVECCION,
    )
    from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.humedad_absoluta import (
        DIFUSIVIDAD_HUMEDAD,
    )
    from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.presion import (
        DIFUSIVIDAD_PRESION,
    )
    from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.temperatura_atmosferica import (
        DIFUSIVIDAD_TERMICA,
    )

    dt = SEGUNDOS_SIMULADOS_TICK
    area = TAMANHO_CELDA_ATMOSFERICA**2
    adveccion = _N_VECINOS * FRACCION_MAXIMA_ADVECCION

    # nombre -> (difusividad, ¿se advecta?)
    magnitudes = {
        "temperatura": (DIFUSIVIDAD_TERMICA, True),
        "presión": (DIFUSIVIDAD_PRESION, False),
        "humedad": (DIFUSIVIDAD_HUMEDAD, True),
        "nube": (0.0, True),  # solo advección, sin difusión: 0.8 <= 1
    }
    fallos = []
    for nombre, (d, advecta) in magnitudes.items():
        salida = d / area * dt * _N_VECINOS + (adveccion if advecta else 0.0)
        if salida > 1.0 + _TOLERANCIA:
            fallos.append(f"{nombre}: salida máxima por tick {salida:.3f} > 1")

    # Lluvia: la autoconversión quita dt/TAU del exceso de nube en un tick.
    # Si dt/TAU > 1 se retiraría más nube de la que hay por encima del umbral.
    if TAU_LLUVIA <= 0 or dt / TAU_LLUVIA > 1.0 + _TOLERANCIA:
        fallos.append(
            f"lluvia: TAU_LLUVIA={TAU_LLUVIA} s exige 0 < dt/TAU <= 1 (dt={dt} s)"
        )
    if fallos:
        raise ValueError(
            "Simulación atmosférica inestable (revisa dt, tamaño de celda, "
            "difusividades o FRACCION_MAXIMA_ADVECCION): " + "; ".join(fallos)
        )
