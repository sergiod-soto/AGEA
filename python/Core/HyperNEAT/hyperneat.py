"""
hyperneat.py
------------
Implementacion de HyperNEAT desde cero, sin dependencias extra
mas alla de neat-python y numpy.

Instalar: pip install neat-python numpy
"""

import numpy as np
import neat


# ===========================================================================
# PARTE 1: SUBSTRATO
# Defines la geometria de la red neuronal grande (el "cerebro" real).
# Las neuronas tienen posicion en [-1, 1] x [-1, 1].
# Esa posicion es lo que la CPPN usa para calcular los pesos.
# ===========================================================================

class Substrate:
    """
    Un substrato es simplemente una lista de coordenadas para cada capa.
    No tiene pesos todavia — la CPPN los generara.
    """

    def __init__(self, input_coords, hidden_coords, output_coords):
        """
        Args:
            input_coords:  lista de (x, y) para neuronas de entrada
            hidden_coords: lista de (x, y) para neuronas ocultas
            output_coords: lista de (x, y) para neuronas de salida
        Todas las coordenadas en [-1.0, 1.0]
        """
        self.input_coords  = input_coords
        self.hidden_coords = hidden_coords
        self.output_coords = output_coords

    @classmethod
    def lineal(cls, n_entradas, n_ocultas, n_salidas):
        """
        Crea un substrato con las neuronas distribuidas en linea horizontal.
        La capa de entrada esta en y=-1, oculta en y=0, salida en y=1.
        """
        def fila(n, y):
            if n == 1:
                return [(0.0, y)]
            return [(2.0 * i / (n - 1) - 1.0, y) for i in range(n)]

        return cls(
            input_coords  = fila(n_entradas, -1.0),
            hidden_coords = fila(n_ocultas,   0.0),
            output_coords = fila(n_salidas,    1.0),
        )

    @classmethod
    def grid(cls, filas_entrada, cols_entrada, n_ocultas, n_salidas):
        """
        Crea un substrato donde la entrada es una rejilla 2D.
        Util para tareas con estructura espacial (vision, sensores en plano).
        """
        coords_entrada = []
        for f in range(filas_entrada):
            for c in range(cols_entrada):
                x = 2.0 * c / (cols_entrada - 1) - 1.0 if cols_entrada > 1 else 0.0
                y = 2.0 * f / (filas_entrada - 1) - 1.0 if filas_entrada > 1 else 0.0
                coords_entrada.append((x, y))

        def fila(n, y):
            if n == 1:
                return [(0.0, y)]
            return [(2.0 * i / (n - 1) - 1.0, y) for i in range(n)]

        return cls(
            input_coords  = coords_entrada,
            hidden_coords = fila(n_ocultas, 0.5),
            output_coords = fila(n_salidas, 1.0),
        )

    def describir(self):
        print(f"Substrato:")
        print(f"  Entrada:  {len(self.input_coords)} neuronas  -> {self.input_coords}")
        print(f"  Oculta:   {len(self.hidden_coords)} neuronas -> {self.hidden_coords}")
        print(f"  Salida:   {len(self.output_coords)} neuronas -> {self.output_coords}")


# ===========================================================================
# PARTE 2: RED HYPERNEAT
# Dado un genoma NEAT (que codifica la CPPN), construye la red del substrato
# consultando la CPPN para cada par de neuronas.
# ===========================================================================

class HyperNEATNetwork:
    """
    Red neuronal construida por una CPPN sobre un substrato.

    El proceso es:
    1. Para cada par (neurona_origen, neurona_destino) entre capas consecutivas:
       - Pasar sus coordenadas a la CPPN: activate([x1, y1, x2, y2, dist])
       - La CPPN devuelve un valor en [-1, 1]: ese es el peso
       - Si |peso| < umbral, la conexion no existe (se pone a 0)
    2. Guardar las matrices de pesos resultantes
    3. La propagacion hacia adelante es una red feed-forward normal con tanh
    """

    def __init__(self, cppn, substrate, umbral=0.2):
        """
        Args:
            cppn:      FeedForwardNetwork de neat-python (la CPPN evolucionada)
            substrate: instancia de Substrate con las coordenadas
            umbral:    conexiones con |w| < umbral se eliminan (tipico: 0.1-0.3)
        """
        self.substrate = substrate
        self.umbral    = umbral
        self.n_conexiones = 0
        self.n_posibles   = 0

        # Construir las matrices de pesos capa por capa
        capas = []
        if substrate.input_coords:
            capas.append(substrate.input_coords)
        if substrate.hidden_coords:
            capas.append(substrate.hidden_coords)
        if substrate.output_coords:
            capas.append(substrate.output_coords)

        self.matrices = []
        for origen, destino in zip(capas[:-1], capas[1:]):
            W = self._construir_matriz(cppn, origen, destino)
            self.matrices.append(W)

    def _construir_matriz(self, cppn, origen, destino):
        """
        Construye una matriz de pesos entre dos capas del substrato.
        Filas = neuronas destino, columnas = neuronas origen.
        """
        n_dest   = len(destino)
        n_origen = len(origen)
        W = np.zeros((n_dest, n_origen))

        for i, (x2, y2) in enumerate(destino):
            for j, (x1, y1) in enumerate(origen):
                dist = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

                # Preguntarle a la CPPN: ¿con que fuerza conectas estas dos posiciones?
                # Entradas: posicion origen, posicion destino, distancia entre ellas
                salida_cppn = cppn.activate([x1, y1, x2, y2, dist])
                w = salida_cppn[0]  # peso en [-1, 1]

                self.n_posibles += 1
                if abs(w) > self.umbral:
                    W[i, j] = w
                    self.n_conexiones += 1

        return W

    def activate(self, inputs):
        """
        Propagacion hacia adelante por el substrato.
        Aplica tanh en cada capa (igual que una red neuronal normal).
        """
        señal = np.array(inputs, dtype=float)
        for W in self.matrices:
            señal = np.tanh(W @ señal)
        return señal.tolist()

    def info_conexiones(self):
        pct = 100 * self.n_conexiones / max(1, self.n_posibles)
        return f"{self.n_conexiones}/{self.n_posibles} conexiones activas ({pct:.1f}%)"


# ===========================================================================
# PARTE 3: EJEMPLO 1 — XOR
# El problema mas simple para verificar que todo funciona.
# ===========================================================================

# Substrato: 2 entradas + bias, 4 ocultas, 1 salida
SUBSTRATE_XOR = Substrate.lineal(n_entradas=3, n_ocultas=4, n_salidas=1)

# Datos XOR (con bias=1 como tercer input, convencion habitual)
XOR_INPUTS  = [(0, 0, 1), (0, 1, 1), (1, 0, 1), (1, 1, 1)]
XOR_TARGETS = [0,          1,          1,          0        ]


def eval_xor(genomes, config):
    """Funcion de evaluacion para NEAT: calcula el fitness de cada genoma."""
    for genome_id, genome in genomes:
        cppn = neat.nn.FeedForwardNetwork.create(genome, config)
        red  = HyperNEATNetwork(cppn, SUBSTRATE_XOR, umbral=0.2)

        error = 0.0
        for xi, yo in zip(XOR_INPUTS, XOR_TARGETS):
            salida = red.activate(list(xi))[0]
            error += (salida - yo) ** 2

        # Fitness: 1 cuando error=0, 0 cuando error=4 (maximo)
        genome.fitness = max(0.0, 1.0 - error / len(XOR_INPUTS))


def run_xor(config_path, n_generaciones=300):
    print("=" * 50)
    print("EJEMPLO 1: XOR con HyperNEAT")
    print("=" * 50)
    SUBSTRATE_XOR.describir()

    config = neat.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path,
    )
    registrar_activaciones_cppn(config)   # <- esto es lo nuevo
    poblacion = neat.Population(config)
    poblacion.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    poblacion.add_reporter(stats)

    ganador = poblacion.run(eval_xor, n_generaciones)

    # Probar el ganador
    print("\n--- Resultado del ganador ---")
    cppn_ganador = neat.nn.FeedForwardNetwork.create(ganador, config)
    red_ganadora = HyperNEATNetwork(cppn_ganador, SUBSTRATE_XOR, umbral=0.2)
    print(f"Conexiones en el substrato: {red_ganadora.info_conexiones()}")
    print()
    for xi, yo in zip(XOR_INPUTS, XOR_TARGETS):
        salida = red_ganadora.activate(list(xi))[0]
        correcto = "OK" if abs(salida - yo) < 0.5 else "MAL"
        print(f"  XOR{xi[:2]} = {yo}  ->  red dice {salida:+.3f}  [{correcto}]")

    return ganador


# ===========================================================================
# PARTE 4: EJEMPLO 2 — CLASIFICACION EN PLANO 2D
# Demonstra como usar un substrato con entrada espacial.
# La red aprende a clasificar puntos segun su cuadrante.
# ===========================================================================

# Substrato con entrada 3x3 (9 neuronas en rejilla), 4 ocultas, 1 salida
SUBSTRATE_2D = Substrate.grid(
    filas_entrada=3, cols_entrada=3,
    n_ocultas=6,
    n_salidas=1,
)

def generar_datos_cuadrante(n=200, seed=42):
    """
    Genera puntos 2D y etiquetas:
    - Etiqueta 1 si el punto esta en cuadrante I o III (producto x*y > 0)
    - Etiqueta 0 si esta en cuadrante II o IV
    """
    rng = np.random.default_rng(seed)
    puntos  = rng.uniform(-1, 1, (n, 2))
    targets = ((puntos[:, 0] * puntos[:, 1]) > 0).astype(float)
    return puntos, targets

PUNTOS_TRAIN, TARGETS_TRAIN = generar_datos_cuadrante(n=100, seed=0)
PUNTOS_TEST,  TARGETS_TEST  = generar_datos_cuadrante(n=100, seed=1)


def eval_cuadrante(genomes, config):
    for genome_id, genome in genomes:
        cppn = neat.nn.FeedForwardNetwork.create(genome, config)
        red  = HyperNEATNetwork(cppn, SUBSTRATE_2D, umbral=0.15)

        correcto = 0
        for (px, py), target in zip(PUNTOS_TRAIN, TARGETS_TRAIN):
            # Las coordenadas del punto son las entradas de la red
            # El substrato tiene 9 entradas (rejilla 3x3), pasamos el punto
            # repetido para llenar la rejilla — version simplificada
            inputs = [px, py, px*py,
                      px, py, px*py,
                      px, py, px*py]
            salida = red.activate(inputs)[0]
            pred   = 1 if salida > 0 else 0
            if pred == int(target):
                correcto += 1

        genome.fitness = correcto / len(PUNTOS_TRAIN)


def run_cuadrante(config_path, n_generaciones=200):
    print("\n" + "=" * 50)
    print("EJEMPLO 2: Clasificacion por cuadrante con HyperNEAT")
    print("=" * 50)
    SUBSTRATE_2D.describir()

    config = neat.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path,
    )

    poblacion = neat.Population(config)
    poblacion.add_reporter(neat.StdOutReporter(True))
    poblacion.add_reporter(neat.StatisticsReporter())

    ganador = poblacion.run(eval_cuadrante, n_generaciones)

    # Evaluar en test
    cppn = neat.nn.FeedForwardNetwork.create(ganador, config)
    red  = HyperNEATNetwork(cppn, SUBSTRATE_2D, umbral=0.15)
    print(f"\nConexiones en el substrato: {red.info_conexiones()}")

    correcto = 0
    for (px, py), target in zip(PUNTOS_TEST, TARGETS_TEST):
        inputs = [px, py, px*py, px, py, px*py, px, py, px*py]
        salida = red.activate(inputs)[0]
        if (salida > 0) == (target > 0.5):
            correcto += 1

    accuracy = correcto / len(PUNTOS_TEST)
    print(f"Accuracy en test: {correcto}/{len(PUNTOS_TEST)} = {accuracy*100:.1f}%")
    return ganador


# ===========================================================================
# MAIN
# ===========================================================================

if __name__ == "__main__":
    import os
    config_path = os.path.join(os.path.dirname(__file__), "config_cppn.ini")

    # Cambia a run_xor o run_cuadrante segun quieras probar
    ganador = run_xor(config_path, n_generaciones=300)
    # ganador = run_cuadrante(config_path, n_generaciones=200)
