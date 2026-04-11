"""
hyperneat_api.py
----------------
HyperNEAT como API funcional. Cada paso del algoritmo es una funcion.

Uso tipico:
    config   = crear_config(poblacion=150, generaciones=300)
    substrato = crear_substrato(entradas=3, ocultas=4, salidas=1)
    ganador  = evolucionar(substrato, config, mi_funcion_de_fitness)
    red      = construir_red(ganador, substrato, config)
    salida   = activar_red(red, [0, 1, 1])

Instalar: pip install neat-python numpy
"""

import os
import math
import neat
import numpy as np


# ===========================================================================
# ACTIVACIONES PERSONALIZADAS
# neat-python no incluye 'gauss' ni 'linear' — hay que registrarlas.
# ===========================================================================

def _gauss(x):
    return float(np.exp(-5.0 * x * x))

def _linear(x):
    return float(x)

def _registrar_activaciones(config):
    config.genome_config.activation_defs.add('gauss',  _gauss)
    config.genome_config.activation_defs.add('linear', _linear)


# ===========================================================================
# PASO 1 — CONFIGURACION
# ===========================================================================

def crear_config(
    poblacion=150,
    umbral_fitness=0.97,
    activaciones="sin gauss abs tanh sigmoid linear",
    activacion_inicial="sin",
    tasa_mutacion_activacion=0.2,
    tasa_añadir_conexion=0.5,
    tasa_borrar_conexion=0.5,
    tasa_añadir_nodo=0.2,
    tasa_borrar_nodo=0.2,
    tasa_mutacion_peso=0.8,
    fuerza_mutacion_peso=0.5,
    umbral_especie=3.0,
    estancamiento_max=20,
    elitismo=2,
):
    """
    Crea y devuelve la configuracion de NEAT para la CPPN.

    Parametros:
        poblacion              -- numero de individuos por generacion
        umbral_fitness         -- fitness al que para la evolucion (0.0 a 1.0)
        activaciones           -- funciones disponibles para los nodos de la CPPN
                                  (separadas por espacios)
        activacion_inicial     -- funcion de activacion con la que nace cada nodo
        tasa_mutacion_activacion -- probabilidad de cambiar la activacion de un nodo
        tasa_añadir_conexion   -- probabilidad de añadir una conexion nueva
        tasa_borrar_conexion   -- probabilidad de eliminar una conexion
        tasa_añadir_nodo       -- probabilidad de añadir un nodo oculto
        tasa_borrar_nodo       -- probabilidad de eliminar un nodo oculto
        tasa_mutacion_peso     -- probabilidad de mutar un peso
        fuerza_mutacion_peso   -- desviacion estandar del ruido al mutar un peso
        umbral_especie         -- distancia maxima para estar en la misma especie
        estancamiento_max      -- generaciones sin mejorar antes de extinguir especie
        elitismo               -- cuantos individuos pasan sin cambios a la siguiente gen

    Devuelve:
        objeto Config de neat-python, listo para pasar a evolucionar()
    """
    contenido = f"""
    [NEAT]
    fitness_criterion      = max
    fitness_threshold      = {umbral_fitness}
    no_fitness_termination = False
    pop_size               = {poblacion}
    reset_on_extinction    = False

    [DefaultGenome]
    num_inputs             = 5
    num_outputs            = 1
    num_hidden             = 0
    initial_connection     = full_direct
    feed_forward           = True

    activation_default     = {activacion_inicial}
    activation_mutate_rate = {tasa_mutacion_activacion}
    activation_options     = {activaciones}

    aggregation_default    = sum
    aggregation_mutate_rate = 0.05
    aggregation_options    = sum

    bias_init_mean         = 0.0
    bias_init_stdev        = 1.0
    bias_max_value         = 3.0
    bias_min_value         = -3.0
    bias_mutate_power      = 0.5
    bias_mutate_rate       = 0.7
    bias_replace_rate      = 0.1

    response_init_mean     = 1.0
    response_init_stdev    = 0.0
    response_max_value     = 3.0
    response_min_value     = -3.0
    response_mutate_power  = 0.0
    response_mutate_rate   = 0.0
    response_replace_rate  = 0.0

    compatibility_disjoint_coefficient = 1.0
    compatibility_weight_coefficient   = 0.5

    conn_add_prob          = {tasa_añadir_conexion}
    conn_delete_prob       = {tasa_borrar_conexion}
    enabled_default        = True
    enabled_mutate_rate    = 0.01

    node_add_prob          = {tasa_añadir_nodo}
    node_delete_prob       = {tasa_borrar_nodo}

    weight_init_mean       = 0.0
    weight_init_stdev      = 1.0
    weight_max_value       = 3.0
    weight_min_value       = -3.0
    weight_mutate_power    = {fuerza_mutacion_peso}
    weight_mutate_rate     = {tasa_mutacion_peso}
    weight_replace_rate    = 0.1

    [DefaultSpeciesSet]
    compatibility_threshold = {umbral_especie}

    [DefaultStagnation]
    species_fitness_func   = max
    max_stagnation         = {estancamiento_max}
    species_elitism        = 2

    [DefaultReproduction]
    elitism                = {elitismo}
    survival_threshold     = 0.2
    """
    
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_config_tmp.ini")
    
    with open(ruta, "w") as f:
        f.write(contenido)

    config = neat.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        ruta,
    )
    _registrar_activaciones(config)
    return config


# ===========================================================================
# PASO 2 — SUBSTRATO
# ===========================================================================

def crear_substrato(entradas, ocultas, salidas):
    """
    Substrato simple: todas las capas en linea horizontal.
    Entrada en y=-1, oculta en y=0, salida en y=+1.
    Las neuronas de cada capa se distribuyen uniformemente en x=[-1, +1].

    Parametros:
        entradas -- numero de neuronas de entrada (int)
        ocultas  -- numero de neuronas ocultas (int, puede ser 0)
        salidas  -- numero de neuronas de salida (int)

    Devuelve:
        dict con claves 'entrada', 'oculta', 'salida',
        cada una con una lista de tuplas (x, y)
    """
    def _fila(n, y):
        if n == 0:
            return []
        if n == 1:
            return [(0.0, y)]
        return [(2.0 * i / (n - 1) - 1.0, y) for i in range(n)]

    return {
        "entrada": _fila(entradas, -1.0),
        "oculta":  _fila(ocultas,   0.0),
        "salida":  _fila(salidas,    1.0),
    }


def crear_substrato_grid(filas_entrada, cols_entrada, ocultas, salidas):
    """
    Substrato con entrada en rejilla 2D.
    Util cuando las entradas tienen estructura espacial
    (camara, sensores en plano, etc).

    Parametros:
        filas_entrada -- filas de la rejilla de entrada
        cols_entrada  -- columnas de la rejilla de entrada
        ocultas       -- numero de neuronas ocultas
        salidas       -- numero de neuronas de salida

    Devuelve:
        dict igual que crear_substrato()
    """
    coords = []
    for f in range(filas_entrada):
        for c in range(cols_entrada):
            x = 2.0 * c / (cols_entrada - 1) - 1.0 if cols_entrada > 1 else 0.0
            y = 2.0 * f / (filas_entrada - 1) - 1.0 if filas_entrada > 1 else 0.0
            coords.append((x, y))

    def _fila(n, y):
        if n == 0: return []
        if n == 1: return [(0.0, y)]
        return [(2.0 * i / (n - 1) - 1.0, y) for i in range(n)]

    return {
        "entrada": coords,
        "oculta":  _fila(ocultas, 0.5),
        "salida":  _fila(salidas, 1.0),
    }


def crear_substrato_custom(coords_entrada, coords_oculta, coords_salida):
    """
    Substrato con coordenadas completamente personalizadas.
    Usa esto cuando la geometria del problema es especifica
    (sensores en circulo, topologia irregular, etc).

    Parametros:
        coords_entrada -- lista de tuplas (x, y) para las entradas
        coords_oculta  -- lista de tuplas (x, y) para las neuronas ocultas
        coords_salida  -- lista de tuplas (x, y) para las salidas

    Ejemplo:
        # Sensores en circulo, un motor en el centro
        import math
        sensores = [(math.cos(2*math.pi*i/8), math.sin(2*math.pi*i/8)) for i in range(8)]
        substrato = crear_substrato_custom(sensores, [(0,0)], [(0, 0.5)])
    """
    return {
        "entrada": list(coords_entrada),
        "oculta":  list(coords_oculta),
        "salida":  list(coords_salida),
    }


# ===========================================================================
# PASO 3 — EVOLUCION
# ===========================================================================

def evolucionar(substrato, config, funcion_fitness, generaciones=300, verbose=True):
    """
    Ejecuta el bucle evolutivo de HyperNEAT.

    En cada generacion, para cada individuo (CPPN):
        1. Construye la red del substrato usando la CPPN
        2. Llama a funcion_fitness(red) para obtener el fitness
        3. NEAT selecciona, muta y cruza los mejores

    Parametros:
        substrato        -- dict creado con crear_substrato() o similar
        config           -- Config creada con crear_config()
        funcion_fitness  -- funcion que recibe una red (dict con 'matrices' y
                            'activar') y devuelve un float (el fitness)
        generaciones     -- numero maximo de generaciones
        verbose          -- si True, imprime el progreso por pantalla

    Devuelve:
        el genoma ganador (el de mayor fitness encontrado)

    Ejemplo de funcion_fitness:
        def mi_fitness(red):
            salida = red['activar']([0.5, -0.3, 1.0])
            return 1.0 - abs(salida[0] - 0.7)
    """
    def _eval(genomes, config):
        for _, genome in genomes:
            cppn = neat.nn.FeedForwardNetwork.create(genome, config)
            red  = construir_red(cppn, substrato)
            genome.fitness = float(funcion_fitness(red))

    poblacion = neat.Population(config)

    if verbose:
        poblacion.add_reporter(neat.StdOutReporter(True))
        poblacion.add_reporter(neat.StatisticsReporter())

    ganador = poblacion.run(_eval, generaciones)
    return ganador


# ===========================================================================
# PASO 4 — CONSTRUIR RED
# ===========================================================================

def construir_red(cppn_o_genoma, substrato, umbral=0.2, config=None):
    """
    Construye la red neuronal del substrato usando una CPPN.

    Para cada par de neuronas entre capas consecutivas, pregunta a la CPPN:
        peso = CPPN(x_origen, y_origen, x_destino, y_destino, distancia)
    Si |peso| > umbral, la conexion existe. Si no, se descarta.

    Parametros:
        cppn_o_genoma -- puede ser:
                         - un FeedForwardNetwork de neat-python (si ya lo tienes)
                         - un genoma de neat-python (necesita config)
        substrato     -- dict creado con crear_substrato() o similar
        umbral        -- minimo |peso| para que exista una conexion (default 0.2)
                         valores tipicos: 0.1 (red densa) a 0.4 (red dispersa)
        config        -- Config de neat-python (solo necesario si pasas un genoma)

    Devuelve:
        dict con:
            'matrices'    -- lista de np.arrays con los pesos por capa
            'activar'     -- funcion callable: activar(inputs) -> outputs
            'conexiones'  -- numero de conexiones activas
            'posibles'    -- numero de conexiones posibles
            'substrato'   -- el substrato usado
    """
    if config is not None:
        cppn = neat.nn.FeedForwardNetwork.create(cppn_o_genoma, config)
    else:
        cppn = cppn_o_genoma

    capas = []
    if substrato["entrada"]: capas.append(substrato["entrada"])
    if substrato["oculta"]:  capas.append(substrato["oculta"])
    if substrato["salida"]:  capas.append(substrato["salida"])

    matrices    = []
    n_activas   = 0
    n_posibles  = 0

    for origen, destino in zip(capas[:-1], capas[1:]):
        W = np.zeros((len(destino), len(origen)))
        for i, (x2, y2) in enumerate(destino):
            for j, (x1, y1) in enumerate(origen):
                d = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                w = cppn.activate([x1, y1, x2, y2, d])[0]
                n_posibles += 1
                if abs(w) > umbral:
                    W[i, j] = w
                    n_activas += 1
        matrices.append(W)

    def _activar(inputs):
        senal = np.array(inputs, dtype=float)
        for W in matrices:
            senal = np.tanh(W @ senal)
        return senal.tolist()

    return {
        "matrices":   matrices,
        "activar":    _activar,
        "conexiones": n_activas,
        "posibles":   n_posibles,
        "substrato":  substrato,
    }


# ===========================================================================
# PASO 5 — USAR LA RED
# ===========================================================================

def activar_red(red, inputs):
    """
    Ejecuta la red con una lista de inputs y devuelve la salida.

    Parametros:
        red    -- dict devuelto por construir_red()
        inputs -- lista de floats, uno por neurona de entrada

    Devuelve:
        lista de floats, uno por neurona de salida

    Ejemplo:
        salida = activar_red(red, [0.0, 1.0, 1.0])
        print(salida)  # [0.823]
    """
    return red["activar"](inputs)


def info_red(red):
    """
    Devuelve un string con informacion sobre la red construida.

    Parametros:
        red -- dict devuelto por construir_red()

    Devuelve:
        string con numero de conexiones activas, posibles y porcentaje
    """
    c = red["conexiones"]
    p = red["posibles"]
    pct = 100 * c / max(1, p)
    return f"{c}/{p} conexiones activas ({pct:.1f}%)"


# ===========================================================================
# UTILIDADES
# ===========================================================================

def red_desde_ganador(ganador, substrato, config, umbral=0.2):
    """
    Atajo: construye directamente la red a partir del genoma ganador.
    Equivale a llamar construir_red(ganador, substrato, umbral, config).

    Parametros:
        ganador   -- genoma devuelto por evolucionar()
        substrato -- dict creado con crear_substrato() o similar
        config    -- Config creada con crear_config()
        umbral    -- minimo |peso| para que exista una conexion

    Devuelve:
        dict igual que construir_red()
    """
    return construir_red(ganador, substrato, umbral=umbral, config=config)


def describir_substrato(substrato):
    """
    Imprime las coordenadas del substrato de forma legible.

    Parametros:
        substrato -- dict creado con crear_substrato() o similar
    """
    print("Substrato:")
    print(f"  Entrada : {len(substrato['entrada'])} neuronas -> {substrato['entrada']}")
    print(f"  Oculta  : {len(substrato['oculta'])}  neuronas -> {substrato['oculta']}")
    print(f"  Salida  : {len(substrato['salida'])}  neuronas -> {substrato['salida']}")


# ===========================================================================
# EJEMPLO: XOR
# Ejecutar directamente: python hyperneat_api.py
# ===========================================================================

if __name__ == "__main__":

    # --- 1. Configuracion ---
    config = crear_config(
        poblacion=150,
        umbral_fitness=0.97,
    )

    # --- 2. Substrato ---
    substrato = crear_substrato(entradas=3, ocultas=4, salidas=1)
    describir_substrato(substrato)

    # --- 3. Funcion de fitness ---
    XOR_CASOS = [
        ([0, 0, 1], 0),
        ([0, 1, 1], 1),
        ([1, 0, 1], 1),
        ([1, 1, 1], 0),
    ]

    def fitness_xor(red):
        error = 0.0
        for inputs, target in XOR_CASOS:
            salida = activar_red(red, inputs)[0]
            error += (salida - target) ** 2
        return max(0.0, 1.0 - error / len(XOR_CASOS))

    # --- 4. Evolucion ---
    ganador = evolucionar(substrato, config, fitness_xor, generaciones=300)

    # --- 5. Usar la red ganadora ---
    red = red_desde_ganador(ganador, substrato, config, umbral=0.2)

    print("\n--- Red ganadora ---")
    print(info_red(red))
    print()
    for inputs, target in XOR_CASOS:
        salida = activar_red(red, inputs)[0]
        ok = "OK" if abs(salida - target) < 0.5 else "MAL"
        print(f"  XOR{inputs[:2]} = {target}  ->  {salida:+.3f}  [{ok}]")