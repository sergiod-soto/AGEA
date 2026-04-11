"""
ejemplos_fitness.py
-------------------
Tres ejemplos de funciones de fitness para HyperNEAT.
Cada una muestra un patron diferente.

Ejecutar: python ejemplos_fitness.py
"""

from hyperneat_api import (
    crear_config, crear_substrato, crear_substrato_custom,
    evolucionar, red_desde_ganador, activar_red, info_red,
    describir_substrato,
)
import math
import random


# ===========================================================================
# EJEMPLO 1 — CLASIFICACION
# La red aprende a distinguir si un numero es mayor o menor que 0.5.
# Es el ejemplo mas simple posible de fitness.
#
# Patron:
#   - Generas casos de prueba (input, respuesta_correcta)
#   - Ejecutas la red en cada caso
#   - El fitness es el porcentaje de aciertos
# ===========================================================================

def fitness_clasificacion(red):
    """
    Tarea: dado un numero x entre 0 y 1, decir si es > 0.5 (salida > 0)
    o <= 0.5 (salida < 0).

    Estructura de la funcion:
        1. Define los casos de prueba
        2. Pasa cada caso por la red
        3. Compara la salida con la respuesta correcta
        4. Devuelve el porcentaje de aciertos (0.0 a 1.0)
    """
    casos = [
        # (inputs,          respuesta_correcta)
        ([0.1, 1.0],        -1),   # 0.1 < 0.5 → salida negativa
        ([0.3, 1.0],        -1),
        ([0.4, 1.0],        -1),
        ([0.6, 1.0],        +1),   # 0.6 > 0.5 → salida positiva
        ([0.8, 1.0],        +1),
        ([0.9, 1.0],        +1),
    ]
    # El segundo input es el bias (siempre 1.0), convencion habitual

    aciertos = 0
    for inputs, respuesta_correcta in casos:
        salida = activar_red(red, inputs)[0]

        # La salida es un float en [-1, 1].
        # Interpretamos: positivo = clase A, negativo = clase B
        prediccion = +1 if salida > 0 else -1

        if prediccion == respuesta_correcta:
            aciertos += 1

    return aciertos / len(casos)   # fitness entre 0.0 y 1.0


# ===========================================================================
# EJEMPLO 2 — REGRESION
# La red aprende a aproximar la funcion f(x) = sin(x).
#
# Patron:
#   - Generas puntos de la funcion que quieres aproximar
#   - Mides el error cuadratico medio entre la salida de la red y el valor real
#   - Conviertes el error en fitness (mas error = menos fitness)
# ===========================================================================

def fitness_seno(red):
    """
    Tarea: dado x en [-1, 1], producir una salida cercana a sin(pi * x).

    La red tiene 2 entradas: el valor x, y el bias (1.0).
    La salida es un unico numero que deberia aproximar sin(pi * x).
    """
    # Generamos 20 puntos uniformes en [-1, 1]
    puntos_x = [-1.0 + 2.0 * i / 19 for i in range(20)]

    error_total = 0.0
    for x in puntos_x:
        valor_real = math.sin(math.pi * x)   # lo que deberia producir la red

        salida = activar_red(red, [x, 1.0])[0]

        error_total += (salida - valor_real) ** 2

    error_medio = error_total / len(puntos_x)

    # Convertir error en fitness:
    # error=0   → fitness=1.0  (perfecto)
    # error=0.5 → fitness=0.5
    # error=4   → fitness~0.0  (peor caso)
    return max(0.0, 1.0 - error_medio)


# ===========================================================================
# EJEMPLO 3 — CONTROL (el mas parecido a un uso real)
# Un "robot" minimalista con 3 sensores y 2 motores.
# La tarea: moverse hacia una fuente de luz.
#
# Patron:
#   - Simulas un entorno (aunque sea muy simple)
#   - Dejas que la red controle el agente varios pasos
#   - El fitness mide que tan bien lo hizo el agente en total
# ===========================================================================

def fitness_control_luz(red):
    """
    Simulacion minimalista:
        - El agente esta en la posicion x en [0, 1]
        - Hay una fuente de luz en x=1.0 (el objetivo)
        - 3 sensores: izquierda, centro, derecha
          (miden la intensidad de luz, que aumenta con la proximidad)
        - 2 salidas: motor izquierdo, motor derecho
          (su diferencia determina el giro, su suma el avance)
        - Simulamos 20 pasos
        - Fitness = que tan cerca acabo del objetivo
    """
    # Estado inicial: agente en el centro, mirando hacia la derecha
    posicion  = 0.2        # empieza lejos del objetivo
    velocidad = 0.0

    puntuacion_total = 0.0
    N_PASOS = 20

    for _ in range(N_PASOS):
        # --- Calcular sensores ---
        # Intensidad de luz: maxima en x=1.0, decrece con la distancia
        distancia_al_objetivo = abs(1.0 - posicion)

        sensor_izq    = max(0.0, 1.0 - (distancia_al_objetivo + 0.1))
        sensor_centro = max(0.0, 1.0 - distancia_al_objetivo)
        sensor_der    = max(0.0, 1.0 - (distancia_al_objetivo - 0.1))

        # --- Pasar sensores por la red ---
        # La red recibe los 3 sensores y produce 2 salidas (motores)
        salidas = activar_red(red, [sensor_izq, sensor_centro, sensor_der])
        motor_izq = salidas[0]
        motor_der = salidas[1]

        # --- Actualizar posicion ---
        # La suma de los motores determina el avance
        avance = (motor_izq + motor_der) * 0.05
        posicion = max(0.0, min(1.0, posicion + avance))

        # --- Acumular puntuacion en este paso ---
        # Recompensa inmediata: cuanto mas cerca del objetivo, mejor
        puntuacion_total += (1.0 - abs(1.0 - posicion))

    # Fitness = puntuacion media por paso (entre 0.0 y 1.0)
    return puntuacion_total / N_PASOS


# ===========================================================================
# EJECUTAR LOS TRES EJEMPLOS
# ===========================================================================

if __name__ == "__main__":

    # -----------------------------------------------------------------------
    # Ejemplo 1: Clasificacion
    # -----------------------------------------------------------------------
    print("=" * 55)
    print("EJEMPLO 1 — Clasificacion (mayor/menor que 0.5)")
    print("=" * 55)

    config    = crear_config(poblacion=100, umbral_fitness=0.99)
    substrato = crear_substrato(entradas=2, ocultas=3, salidas=1)
    describir_substrato(substrato)

    ganador = evolucionar(substrato, config, fitness_clasificacion, generaciones=200)
    red     = red_desde_ganador(ganador, substrato, config)

    print(f"\nRed: {info_red(red)}")
    print("\nResultados:")
    for x in [0.1, 0.3, 0.6, 0.9]:
        salida = activar_red(red, [x, 1.0])[0]
        prediccion = "MAYOR" if salida > 0 else "MENOR"
        correcto   = "MAYOR" if x > 0.5 else "MENOR"
        ok = "OK" if prediccion == correcto else "MAL"
        print(f"  x={x}  salida={salida:+.3f}  pred={prediccion}  [{ok}]")

    # -----------------------------------------------------------------------
    # Ejemplo 2: Regresion
    # -----------------------------------------------------------------------
    print("\n" + "=" * 55)
    print("EJEMPLO 2 — Regresion (aproximar seno)")
    print("=" * 55)

    config    = crear_config(poblacion=150, umbral_fitness=0.95)
    substrato = crear_substrato(entradas=2, ocultas=4, salidas=1)
    describir_substrato(substrato)

    ganador = evolucionar(substrato, config, fitness_seno, generaciones=300)
    red     = red_desde_ganador(ganador, substrato, config)

    print(f"\nRed: {info_red(red)}")
    print("\nResultados (red vs sin(pi*x)):")
    for x in [-0.8, -0.4, 0.0, 0.4, 0.8]:
        salida     = activar_red(red, [x, 1.0])[0]
        valor_real = math.sin(math.pi * x)
        error      = abs(salida - valor_real)
        print(f"  x={x:+.1f}  red={salida:+.3f}  real={valor_real:+.3f}  error={error:.3f}")

    # -----------------------------------------------------------------------
    # Ejemplo 3: Control
    # -----------------------------------------------------------------------
    print("\n" + "=" * 55)
    print("EJEMPLO 3 — Control (robot hacia la luz)")
    print("=" * 55)

    config    = crear_config(poblacion=150, umbral_fitness=0.95)
    substrato = crear_substrato(entradas=3, ocultas=4, salidas=2)
    describir_substrato(substrato)

    ganador = evolucionar(substrato, config, fitness_control_luz, generaciones=300)
    red     = red_desde_ganador(ganador, substrato, config)

    print(f"\nRed: {info_red(red)}")

    # Simular el comportamiento final paso a paso
    print("\nSimulacion del agente ganador:")
    print(f"  Objetivo: x=1.0")
    posicion = 0.2
    for paso in range(20):
        distancia = abs(1.0 - posicion)
        s_izq = max(0.0, 1.0 - (distancia + 0.1))
        s_cen = max(0.0, 1.0 - distancia)
        s_der = max(0.0, 1.0 - (distancia - 0.1))
        salidas  = activar_red(red, [s_izq, s_cen, s_der])
        avance   = (salidas[0] + salidas[1]) * 0.05
        posicion = max(0.0, min(1.0, posicion + avance))
        if paso % 4 == 0:
            barra = int(posicion * 30)
            print(f"  paso {paso:2d}: {'.' * barra}A{'.' * (30 - barra)}|  x={posicion:.3f}")

    print(f"\n  Posicion final: {posicion:.3f}  (objetivo: 1.0, distancia: {abs(1.0-posicion):.3f})")
