# Gestores/Mundo/Sector/registry.py
from Gestores.Mundo.Sector.Funciones import (
    set_sector_mode,
    load_state,
    get_state,
    set_ghost_zone,
    add_migrating_bot,
    set_sounds,
    start_tick,
    get_delta,
    save_snapshot,
)

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
