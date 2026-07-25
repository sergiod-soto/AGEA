# Gestores/Bots/Hypervisor/registry.py



from Infraestructura.Gestores.Bots.Hypervisor.Funciones import (
    freeze,
    resume,
    save_snapshot,
    spawn_bot,
)
from Infraestructura.Gestores.Bots.Hypervisor.Funciones import get_bot_stats, get_bot_status, kill_bot, list_bots, reset_budgets, set_point_budget

FUNCIONES = [
    spawn_bot,
    kill_bot,
    get_bot_stats,
    list_bots,
    reset_budgets,
    set_point_budget,
    get_bot_status,
    freeze,
    resume,
    save_snapshot,
]
