# Gestores/Bots/Gestor_Bots/registry.py
from Gestores.Bots.Gestor_Bots.Funciones import (
    spawn_bot,
    kill_bot,
    notify_bot_death,
    broadcast_budgets,
    reset_budgets,
    freeze_all,
    resume_all,
    save_snapshot,
    register_hypervisor,
    update_hypervisor_load,
    list_hypervisors,
    forward_action,
)

FUNCIONES = [
    spawn_bot,
    kill_bot,
    notify_bot_death,
    broadcast_budgets,
    reset_budgets,
    freeze_all,
    resume_all,
    save_snapshot,
    register_hypervisor,
    update_hypervisor_load,
    list_hypervisors,
    forward_action,
]
