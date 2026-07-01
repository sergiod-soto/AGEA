# Gestores/Mundo/Gestor_Mundo/registry.py
from Infraestructura.Gestores.Mundo.Gestor_Mundo.Funciones import (
    set_tick_rate,
)
from Infraestructura.Gestores.Mundo.Gestor_Mundo.Funciones import create_element, delete_element, despawn_global_event, forward_action, get_active_events, get_global_state, get_snapshot_info, get_world_map, modify_element, pause, resume, set_tick_speed, spawn_global_event, trigger_deep_save

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
    set_tick_rate,
]
