# Gestores/Bots/Gestor_Bots/registry.py
from Infraestructura.Gestores.Bots.Gestor_Bots.Funciones import (
    notify_bot_death,
)
from Infraestructura.Gestores.Bots.Gestor_Bots.Funciones import (
    broadcast_budgets_async,
    forward_action,
    freeze_all,
    kill_bot,
    list_hypervisors,
    register_hypervisor,
    reset_budgets,
    resume_all,
    save_snapshot,
    spawn_bot,
    update_hypervisor_load,
)

FUNCIONES = [
    spawn_bot,
    kill_bot,
    notify_bot_death,
    broadcast_budgets_async,
    reset_budgets,
    freeze_all,
    resume_all,
    save_snapshot,
    register_hypervisor,
    update_hypervisor_load,
    list_hypervisors,
    forward_action,
]
