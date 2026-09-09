# Infraestructura/Gestores/Comunicacion/Remoto/registry.py
"""
registry.py — Registro de operaciones que Comunicaciones_Remoto puede
reenviar. Cada módulo de Funciones/ expone COMPONENTE, OPERACION y
handle(clientes, payload: bytes) -> bytes.
"""

from Infraestructura.Gestores.Comunicacion.Remoto.Funciones import (
    broadcast_budgets,
    consultar_representacion,
    crear_elemento,
    despawn_global_event,
    eliminar_elemento,
    freeze_all,
    get_active_events,
    get_elementos_globales,
    get_snapshot_info,
    list_hypervisors,
    modificar_elemento,
    obtener_audio,
    pause,
    resume,
    resume_all,
    save_snapshot,
    set_tick_rate,
    spawn_global_event,
    trigger_deep_save,
    comando_consola,
    advance_tick,
)

FUNCIONES = [
    # Logica_Mundo
    consultar_representacion,
    obtener_audio,
    spawn_global_event,
    despawn_global_event,
    get_active_events,
    crear_elemento,
    modificar_elemento,
    eliminar_elemento,
    get_elementos_globales,
    # Gestor_Mundo
    pause,
    resume,
    set_tick_rate,
    trigger_deep_save,
    get_snapshot_info,
    # Gestor_Bots
    list_hypervisors,
    broadcast_budgets,
    freeze_all,
    resume_all,
    save_snapshot,
    # Consola
    comando_consola,
    advance_tick,
]
