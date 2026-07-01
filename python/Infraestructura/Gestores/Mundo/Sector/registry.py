# Gestores/Mundo/Sector/registry.py
from Infraestructura.Gestores.Mundo.Sector.Funciones import (
    start_tick,
)
from Infraestructura.Gestores.Mundo.Sector.Funciones import add_migrating_bot, get_delta, get_state, load_state, save_snapshot, set_ghost_zone, set_sector_mode, set_sounds

FUNCIONES = [
    set_sector_mode,
    load_state,
    get_state,
    set_ghost_zone,
    add_migrating_bot,
    start_tick,
    get_delta,
    save_snapshot,
    #
    # ----- funciones añadidas --------
    set_sounds,
]
