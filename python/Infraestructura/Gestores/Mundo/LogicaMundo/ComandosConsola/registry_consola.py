# Infraestructura/Gestores/Mundo/LogicaMundo/ComandosConsola/registry_consola.py
"""
registry_consola.py — Registro de comandos que llegan por el RPC único
EjecutarComandoConsola de LogicaMundoService. Añadir un comando nuevo
no toca el .proto ni el servicer: solo un módulo aquí + su alta.
"""

from Infraestructura.Gestores.Mundo.LogicaMundo.ComandosConsola import (
    obtener_elemento,
)

COMANDOS_CONSOLA = {
    obtener_elemento.TIPO: obtener_elemento,
}
