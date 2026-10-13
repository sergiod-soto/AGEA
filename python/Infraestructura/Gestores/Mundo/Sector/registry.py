# Infraestructura/Gestores/Mundo/Sector/registry.py

from Infraestructura.Gestores.Mundo.Sector.Funciones import (
    shutdown,
    start_tick,
)
from Infraestructura.Gestores.Mundo.Sector.Funciones import (
    get_delta,
    get_state,
    load_state,
    save_snapshot,
    set_ghost_zone,
    set_sector_mode,
    set_sounds,
    recibir_elemento,
    confirmar_salida,
)
from Infraestructura.Gestores.Mundo.Sector.Funciones import (
    set_atmosphere_ghost_zone,
    set_global_cycles,
)

FUNCIONES = [
    set_sector_mode,
    load_state,
    get_state,
    set_ghost_zone,
    start_tick,
    get_delta,
    save_snapshot,
    shutdown,
    set_sounds,
    recibir_elemento,
    confirmar_salida,
    #
    # ----- sistema atmosférico --------
    set_atmosphere_ghost_zone,
    set_global_cycles,
]
