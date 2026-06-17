import math


def _bresenham_celdas(x0: int, y0: int, angulo: float, distancia: int) -> list[tuple[int, int]]:
    """
    Genera la lista de celdas que atraviesa un rayo desde (x0, y0)
    en la dirección `angulo` (0-360 grados) hasta `distancia` celdas.
    Usa el algoritmo de Bresenham generalizado.
    """
    rad = math.radians(angulo)
    dx = math.cos(rad)
    dy = math.sin(rad)

    celdas = []
    x, y = float(x0), float(y0)

    for _ in range(distancia):
        x += dx
        y += dy
        cx, cy = int(math.floor(x)), int(math.floor(y))
        if not celdas or celdas[-1] != (cx, cy):
            celdas.append((cx, cy))

    return celdas