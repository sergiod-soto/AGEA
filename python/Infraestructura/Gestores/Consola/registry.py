# Infraestructura/Gestores/Consola/registry.py
"""
registry.py — Registro de acciones disponibles en la consola. Añadir
una acción nueva no requiere tocar consola.py: basta crear el módulo
en Acciones/ (con una variable ACCION: AccionConsola) y darlo de alta
aquí.
"""

from Infraestructura.Gestores.Consola.Acciones import (
    pausar,
    reanudar,
    modo_paso,
    avanzar_tick,
    salida_unity,
    tick_rate,
    crear_elemento,
    datos,
    obtener_elemento,
)

_MODULOS = (
    pausar,
    reanudar,
    modo_paso,
    avanzar_tick,
    tick_rate,
    crear_elemento,
    datos,
    salida_unity,
    obtener_elemento,
)

ACCIONES = {modulo.ACCION.nombre: modulo.ACCION for modulo in _MODULOS}
