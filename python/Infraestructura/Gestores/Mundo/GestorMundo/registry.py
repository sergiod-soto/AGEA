# Infraestructura/Gestores/Mundo/Gestor_Mundo/registry.py
"""
Recortado tras el refactor a Logica_Mundo: solo quedan las operaciones
de mecánica de tick que gestor_mundo sigue implementando. El resto
(eventos globales, alta/edición/baja de elementos, ForwardAction) se
resuelve ahora contra LogicaMundoService — ver Logica_Mundo/registry.py.
"""

from Infraestructura.Gestores.Mundo.GestorMundo.Funciones import (
    get_snapshot_info,
    heartbeat,
    pause,
    resume,
    set_tick_rate,
    trigger_deep_save,
    shutdown,
)

FUNCIONES = [
    get_snapshot_info,
    pause,
    resume,
    trigger_deep_save,
    set_tick_rate,
    heartbeat,
    shutdown,
]
