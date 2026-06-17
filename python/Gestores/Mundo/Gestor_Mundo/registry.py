# Gestores/Mundo/Gestor_Mundo/registry.py
from Gestores.Mundo.Gestor_Mundo.Funciones import (
    get_world_map,
    get_global_state,
    get_snapshot_info,
    pause,
    resume,
    set_tick_speed,
    trigger_deep_save,
    spawn_global_event,
    despawn_global_event,
    get_active_events,
    modify_element,
    create_element,
    delete_element,
    forward_action,
)

# Para añadir una función nueva: importarla arriba y añadirla aquí.
FUNCIONES = [
    get_world_map,
    get_global_state,
    get_snapshot_info,
    pause,
    resume,
    set_tick_speed,
    trigger_deep_save,
    spawn_global_event,
    despawn_global_event,
    get_active_events,
    modify_element,
    create_element,
    delete_element,
    forward_action,
]
