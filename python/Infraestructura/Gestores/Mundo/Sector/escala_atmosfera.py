# Infraestructura/Gestores/Mundo/Sector/escala_atmosfera.py
"""
Conversión de posición de TERRENO a posición de ATMÓSFERA (bloques de
ATMOSFERA_ESCALA celdas), compartida por TickContext y Sector -- antes
duplicada como `x // escala` en ambos sitios. Vive en su propio módulo,
sin depender de tick_context.py ni de sector, para que ambos puedan
importarla sin crear un ciclo (sector ya importa TickContext de
tick_context.py -- si tick_context.py importase algo de sector,
sería circular).
"""


def pos_terreno_a_atmosfera(x: int, y: int, escala: int) -> tuple[int, int]:
    return (x // escala, y // escala)
