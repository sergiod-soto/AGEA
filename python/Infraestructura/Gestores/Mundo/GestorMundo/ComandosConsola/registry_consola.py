# Infraestructura/Gestores/Mundo/Gestor_Mundo/ComandosConsola/registry_consola.py
"""
registry_consola.py — Registro de comandos que llegan por el RPC único
EjecutarComandoConsola (ver gestor_mundo_servicer.py). Añadir un
comando de consola nuevo NO requiere tocar el .proto ni el servicer:
solo crear el módulo aquí y darlo de alta en COMANDOS_CONSOLA.
"""

from Infraestructura.Gestores.Mundo.GestorMundo.ComandosConsola import (
    set_step_mode,
    advance_tick,
)

COMANDOS_CONSOLA = {
    set_step_mode.TIPO: set_step_mode,
    advance_tick.TIPO: advance_tick,
}
