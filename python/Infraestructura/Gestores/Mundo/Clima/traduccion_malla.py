# Infraestructura/Gestores/Mundo/Clima/traduccion_malla.py
"""
Traducción de coordenadas entre la malla de tierra y la malla de clima.

La malla de clima es más gruesa que la de tierra: cada celda de clima cubre
un bloque de factor_n x factor_n celdas de tierra. Ambas mallas comparten
el origen (0, 0) en la esquina inferior izquierda, así que la traducción es
solo división/multiplicación entera — no hace falta ningún desplazamiento.

Precondición asumida (confirmada en el diseño): SECTOR_SIZE (tamaño de
sector de tierra) siempre es múltiplo de factor_n. Esto garantiza que un
sector de tierra nunca queda partido a caballo entre dos celdas de clima
en sus bordes.

Quién usa esto:
  Logica_Mundo, al construir el delta de entrada de cada sector de tierra,
  traduce las celdas de clima correspondientes antes de enviarlas — así el
  sector de tierra nunca necesita conocer la malla de clima, solo recibe
  ya los valores traducidos a su propia granularidad.
"""


def terreno_a_clima(x: int, y: int, factor_n: int) -> tuple[int, int]:
    """Dada una celda de tierra (x, y), devuelve la celda de clima que la
    cubre. Ej: factor_n=2 → (4, 2) pertenece a la celda de clima (2, 1)."""
    return (x // factor_n, y // factor_n)


def clima_a_terreno(cx: int, cy: int, factor_n: int) -> list[tuple[int, int]]:
    """Dada una celda de clima (cx, cy), devuelve todas las celdas de
    tierra que cubre. Ej: factor_n=2 → (2, 1) cubre
    [(4,2), (4,3), (5,2), (5,3)]."""
    x0, y0 = cx * factor_n, cy * factor_n
    return [(x0 + dx, y0 + dy) for dx in range(factor_n) for dy in range(factor_n)]
