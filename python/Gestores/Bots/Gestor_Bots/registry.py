# Gestores/Bots/Gestor_Bots/registry.py
from Gestores.Bots.Gestor_Bots.Funciones import (
    spawn_bot,
    kill_bot,
    broadcast_budgets,
    register_hypervisor,
    update_hypervisor_load,
    list_hypervisors,
    forward_action,
)

FUNCIONES = [
    spawn_bot,
    kill_bot,
    broadcast_budgets,
    register_hypervisor,
    update_hypervisor_load,
    list_hypervisors,
    forward_action,
]
