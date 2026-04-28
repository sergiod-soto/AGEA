import neat
import pickle


# =============================================================================
# ADN EMBEBIDO
# Generado por la gramática a partir del bytearray original.
# Este es el ADN que se usará para la reproducción — no el bytearray
# que generó este código. Puede ser atacado/corrompido por otros bots.
# =============================================================================

_dna = bytearray([
    # PLACEHOLDER — la gramática sustituirá esto por el bytearray real
    0b00000,
])


# =============================================================================
# CONFIGURACIÓN DE LA RED NEURONAL (generada por el ADN)
# HyperNEAT vía neat-python. La topología y pesos iniciales
# están codificados en el ADN. Los pesos evolucionan durante la vida.
# =============================================================================

# Inputs de la red (sensores):
#   0  — energía propia (normalizada 0..1)
#   1  — vida propia (normalizada 0..1)
#   2  — energía del recurso más cercano (0 si no hay)
#   3  — distancia al recurso más cercano (normalizada)
#   4  — ángulo al recurso más cercano (normalizada -1..1)
#   5  — energía del bot más cercano (0 si no hay)
#   6  — distancia al bot más cercano (normalizada)
#   7  — ángulo al bot más cercano (normalizada -1..1)
#   8  — vida del bot más cercano (0 si no hay)
#   9  — ¿el bot más cercano es aliado conocido? (0/1)
#   10 — tick actual (normalizado, para ritmos temporales)
#   11 — energía media de la zona (normalizada)
NN_INPUTS = 12

# Outputs de la red (actuadores):
#   0  — dx movimiento (-1..1)
#   1  — dy movimiento (-1..1)
#   2  — ¿atacar bot cercano? (umbral > 0.5)
#   3  — ¿recolectar recurso? (umbral > 0.5)
#   4  — ¿reproducirse? (umbral > 0.5)
#   5  — ¿buscar pareja sexual? (umbral > 0.5)
#   6  — ¿atacar ADN del objetivo? (umbral > 0.5)
#   7  — tipo de ataque al código: 0=corte 0.33=veneno 0.66=inyección
#   8  — umbral de energía para reproducción (0..1, hardcoded override posible)
NN_OUTPUTS = 9

# Genome generado por el ADN — PLACEHOLDER
# La gramática genera aquí un genome neat serializado como bytes
# que se deserializa al nacer el bot.
_nn_genome_bytes = None  # sustituir por: pickle.dumps(genome_obj)


def _build_network(genome_bytes):
    """Instancia la red a partir del genome codificado en el ADN."""
    if genome_bytes is None:
        return None
    genome = pickle.loads(genome_bytes)
    config = _get_neat_config()
    return neat.nn.FeedForwardNetwork.create(genome, config)


def _get_neat_config():
    """
    Configuración neat-python.
    En producción esto vendría también del ADN o de un archivo externo.
    """
    # PSEUDOCÓDIGO — sustituir por neat.Config real al integrar
    # config = neat.Config(
    #     neat.DefaultGenome,
    #     neat.DefaultReproduction,
    #     neat.DefaultSpeciesSet,
    #     neat.DefaultStagnation,
    #     'neat_config.ini'
    # )
    # return config
    return None


# =============================================================================
# ESTADO INTERNO DEL BOT
# Variables de memoria que persisten entre ticks.
# No se heredan — son fenotípicas puras.
# =============================================================================

_memory = {
    "known_allies":    set(),    # ids de bots con los que hubo cooperación
    "known_threats":   set(),    # ids de bots que causaron daño
    "last_positions":  [],       # historial de posiciones propias (últimos N ticks)
    "resource_map":    {},       # {(x,y): energia_estimada} — mapa interno
    "last_energy":     None,     # energía en el tick anterior
    "last_health":     None,     # vida en el tick anterior
    "ticks_alive":     0,
}


# =============================================================================
# SENSORES — pseudocódigo
# Estas funciones leen la API del sandbox.
# El bot no tiene acceso directo al estado global — solo a lo que
# el sandbox expone dentro del radio de percepción.
# =============================================================================

def _sense(world):
    """
    Lee el entorno y devuelve el vector de inputs para la red neuronal.
    Todas las llamadas a world.* son pseudocódigo — reemplazar con la API real.
    """

    # --- Stats propios ---
    # own_energy = world.get_own_energy()          # float 0..max_energy
    # own_health = world.get_own_health()           # float 0..max_health
    # max_energy = world.get_max_energy()
    # max_health = world.get_max_health()
    # tick       = world.get_current_tick()
    # max_tick   = world.get_max_tick()             # para normalizar

    own_energy = 0.5   # PLACEHOLDER
    own_health = 1.0   # PLACEHOLDER
    max_energy = 1.0
    max_health = 1.0
    tick       = 0
    max_tick   = 10000

    # --- Recurso más cercano ---
    # nearest_resource = world.scan_nearest_resource()
    # Si existe: {energy, distance, angle}
    # nearest_resource = world.scan_nearest_resource()

    res_energy   = 0.0  # PLACEHOLDER
    res_distance = 1.0
    res_angle    = 0.0

    # --- Bot más cercano ---
    # nearest_bot = world.scan_nearest_bot()
    # Si existe: {energy, health, distance, angle, id}

    bot_energy   = 0.0  # PLACEHOLDER
    bot_health   = 0.0
    bot_distance = 1.0
    bot_angle    = 0.0
    bot_id       = None

    is_ally = 1.0 if bot_id in _memory["known_allies"] else 0.0

    # --- Entorno local ---
    # zone_avg_energy = world.get_zone_energy_average()

    zone_energy = 0.5  # PLACEHOLDER

    return [
        own_energy   / max_energy,
        own_health   / max_health,
        res_energy,
        res_distance,
        res_angle,
        bot_energy,
        bot_distance,
        bot_angle,
        bot_health,
        is_ally,
        tick / max_tick,
        zone_energy,
    ], bot_id


# =============================================================================
# ACTUADORES — pseudocódigo
# Traducen los outputs de la red en llamadas al sandbox.
# =============================================================================

def _act(world, nn_outputs, nearest_bot_id):
    """
    Ejecuta las acciones decididas por la red neuronal.
    """
    dx          = nn_outputs[0]   # -1..1
    dy          = nn_outputs[1]   # -1..1
    do_attack   = nn_outputs[2] > 0.5
    do_collect  = nn_outputs[3] > 0.5
    do_reproduce       = nn_outputs[4] > 0.5
    do_seek_partner    = nn_outputs[5] > 0.5
    do_attack_dna      = nn_outputs[6] > 0.5
    attack_type_raw    = nn_outputs[7]
    repro_energy_ratio = nn_outputs[8]   # fracción de energía a dar al hijo

    # Movimiento — siempre ejecutado (la red siempre emite dx/dy)
    # world.move(dx, dy)

    # Recolección
    if do_collect:
        pass
        # world.collect_nearest_resource()

    # Ataque al código del bot más cercano
    if do_attack and nearest_bot_id is not None:
        if attack_type_raw < 0.33:
            # Corte: elimina un bloque de código del objetivo
            # world.attack_cut(nearest_bot_id)
            pass
        elif attack_type_raw < 0.66:
            # Veneno: modifica un bloque de código del objetivo
            # world.attack_poison(nearest_bot_id)
            pass
        else:
            # Inyección: inserta código parasitario en el objetivo
            # world.attack_inject(nearest_bot_id)
            pass

    # Ataque al ADN del bot más cercano (corrupción genética)
    if do_attack_dna and nearest_bot_id is not None:
        pass
        # world.attack_dna(nearest_bot_id)
        # Efecto: corrompe bits aleatorios del _dna del objetivo.
        # No hay efecto inmediato — afecta a la descendencia del objetivo.

    # Reproducción
    if do_reproduce:
        _try_reproduce(world, do_seek_partner, nearest_bot_id, repro_energy_ratio)


# =============================================================================
# REPRODUCCIÓN
# =============================================================================

def _try_reproduce(world, sexual, partner_id, energy_ratio):
    """
    Intenta reproducirse. El mundo extrae _dna de este bot para generar al hijo.
    Si es sexual y hay pareja, el mundo mezcla ambos _dna antes de generar.

    energy_ratio: fracción de la energía propia que se transfiere al hijo.
    El coste mínimo de reproducción está hardcoded en el núcleo —
    si no hay suficiente energía, el mundo rechaza la llamada.
    """
    if sexual and partner_id is not None and partner_id in _memory["known_allies"]:
        pass
        # world.reproduce_sexual(partner_id=partner_id, energy_ratio=energy_ratio)
        # El mundo:
        #   1. Extrae _dna de este bot y del partner
        #   2. Cruza los dos bytearrays (crossover)
        #   3. Aplica tasa de mutación del sistema
        #   4. Genera código nuevo con la gramática
        #   5. Inyecta el núcleo protegido
        #   6. Spawna el hijo con energy_ratio de la energía del padre
    else:
        pass
        # world.reproduce_asexual(energy_ratio=energy_ratio)
        # El mundo:
        #   1. Extrae _dna de este bot
        #   2. Aplica tasa de mutación del sistema
        #   3. Genera código nuevo con la gramática
        #   4. Inyecta el núcleo protegido
        #   5. Spawna el hijo con energy_ratio de la energía del padre


# =============================================================================
# FUNCIONES HARDCODED — no pasan por la red neuronal
# Análogo a reflejos del tallo cerebral: ocurren siempre, sin deliberación.
# =============================================================================

def _hardcoded_responses(world, own_health, own_energy):
    """
    Respuestas automáticas que ocurren antes de que la red procese nada.
    Retorna True si alguna respuesta hardcoded tomó el control del tick.
    """

    # Respuesta de huida crítica — si vida < 10%, moverse en dirección opuesta
    # al bot más cercano sin consultar la red
    if own_health < 0.1:
        pass
        # nearest = world.scan_nearest_bot()
        # if nearest:
        #     world.move(-nearest['dx_normalized'], -nearest['dy_normalized'])
        # return True

    # Inanición crítica — si energía < 5%, recolectar el recurso más cercano
    # sin consultar la red
    if own_energy < 0.05:
        pass
        # world.collect_nearest_resource()
        # return True

    return False


def _update_memory(world, nn_outputs, nearest_bot_id):
    """Actualiza el estado interno con lo observado en este tick."""
    _memory["ticks_alive"] += 1

    # Registrar posición actual
    # pos = world.get_own_position()
    # _memory["last_positions"].append(pos)
    # if len(_memory["last_positions"]) > 20:
    #     _memory["last_positions"].pop(0)

    # Detectar si recibimos daño este tick — registrar al agresor
    # current_health = world.get_own_health()
    # if _memory["last_health"] is not None:
    #     if current_health < _memory["last_health"]:
    #         if nearest_bot_id:
    #             _memory["known_threats"].add(nearest_bot_id)
    #             _memory["known_allies"].discard(nearest_bot_id)

    # Detectar si recibimos energía de otro bot — registrar como aliado
    # current_energy = world.get_own_energy()
    # if _memory["last_energy"] is not None:
    #     energy_delta = current_energy - _memory["last_energy"]
    #     if energy_delta > 0 and nearest_bot_id:
    #         if nearest_bot_id not in _memory["known_threats"]:
    #             _memory["known_allies"].add(nearest_bot_id)

    pass


# =============================================================================
# NÚCLEO — INYECTADO POR EL ÁRBITRO AL NACER
# Este bloque no está en el ADN. Es añadido después de que la gramática
# genera el código. El árbitro verifica su hash cada tick.
# No puede ser modificado por ataques externos.
# =============================================================================
#
# def _core_tick(world):
#     assert isinstance(_dna, bytearray), "ADN corrupto o ausente"
#     stats = world.get_own_stats()
#     if stats['health'] <= 0:
#         world.die()
#     # Hook de servidumbre (a implementar en el futuro):
#     # if world.get_master_signal():
#     #     _execute_master_command(world)


# =============================================================================
# BUCLE PRINCIPAL
# Llamado por el árbitro una vez por tick.
# Estructura: núcleo → hardcoded → sensores → red → actuadores → memoria
# =============================================================================

_network = _build_network(_nn_genome_bytes)

def tick(world):
    """
    Punto de entrada del árbitro cada tick.
    El bot no puede iniciar un nuevo tick hasta que el árbitro lo llame.
    """

    # 1. Núcleo (hardcoded, no modificable)
    # _core_tick(world)

    # 2. Stats básicos para reflejos
    own_health = 1.0   # world.get_own_health() / world.get_max_health()
    own_energy = 0.5   # world.get_own_energy() / world.get_max_energy()

    # 3. Reflejos hardcoded — pueden cortocircuitar el resto del tick
    if _hardcoded_responses(world, own_health, own_energy):
        _update_memory(world, None, None)
        return

    # 4. Sensores → vector de inputs
    if _network is None:
        # Red no inicializada (bot en Fase 0 — solo compila y sobrevive)
        return

    inputs, nearest_bot_id = _sense(world)

    # 5. Red neuronal decide
    nn_outputs = _network.activate(inputs)

    # 6. Actuadores ejecutan
    _act(world, nn_outputs, nearest_bot_id)

    # 7. Actualizar memoria interna
    _update_memory(world, nn_outputs, nearest_bot_id)
