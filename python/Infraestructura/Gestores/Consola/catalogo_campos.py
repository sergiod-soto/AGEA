# Infraestructura/Gestores/Consola/catalogo_campos.py
"""
catalogo_campos.py — Traduce nombres de campo (los que devuelve
Elemento.campos_para_creacion() / Comportamiento.campos_para_creacion())
a un CampoCuestionario real (prompt + parser).

Es la contraparte de consola de esos métodos: la clase solo dice QUÉ
nombres hacen falta (strings, sin conocer nada de Consola -- ver
discusión sobre dirección de dependencias), y aquí se decide CÓMO se
pregunta cada uno por teclado.

Si un nombre de campos_para_creacion() no está aquí, crear_elemento()
falla con un error explícito (ver Acciones/crear_elemento.py) en vez
de omitir el campo en silencio -- así un comportamiento nuevo que
declare un campo hace evidente, la primera vez que se prueba desde
consola, que también hay que darlo de alta aquí.
"""

from Core.Entities.Elementos.elemento import Elemento
from Infraestructura.Gestores.Consola.cuestionario import (
    CampoCuestionario,
    parse_posicion,
)

CATALOGO_CAMPOS: dict[str, CampoCuestionario] = {
    "casilla": CampoCuestionario(
        nombre="casilla",
        prompt="Posición (x,y)",
        tipo=parse_posicion,
    ),
    "tamanho": CampoCuestionario(
        nombre="tamanho",
        prompt="Tamaño",
        tipo=int,
    ),
    "capa": CampoCuestionario(
        nombre="capa",
        prompt="Capa",
        tipo=int,
    ),
    "peso": CampoCuestionario(
        nombre="peso",
        prompt="Peso (kg)",
        tipo=float,
    ),
    "coste_empujar": CampoCuestionario(
        nombre="coste_empujar",
        prompt="Coste Empujar",
        tipo=float,
    ),
    "volumen": CampoCuestionario(
        nombre="volumen",
        prompt="Volumen",
        tipo=float,
    ),
    "rgb_base": CampoCuestionario(
        nombre="rgb_base",
        prompt="RGB Base",
        tipo=tuple[int, int, int],
    ),
    "temperatura_propia": CampoCuestionario(
        nombre="temperatura_propia",
        prompt="Temperatura Propia (ºC)",
        tipo=float,
    ),
    "tasa_transferencia_temperatura": CampoCuestionario(
        nombre="tasa_transferencia_temperatura",
        prompt="Tasa de Transferencia de Temperatura (ºC/s)",
        tipo=float,
    ),
    "agarrado_por": CampoCuestionario(
        nombre="agarrado_por",
        prompt="Agarrado Por",
        tipo=int,
        opcional=True,
        valor_por_defecto=None,
    ),
    "durabilidad_max_destruible": CampoCuestionario(
        nombre="durabilidad_max_destruible",
        prompt="Durabilidad Maxima Destruccion",
        tipo=float,
    ),
    "durabilidad_max_erosion": CampoCuestionario(
        nombre="durabilidad_max_erosion",
        prompt="Durabilidad Maxima Erosion",
        tipo=float,
    ),
    # TODO: completar a medida que cada Comportamiento de Piedra (y
    # demás elementos) implemente su campos_para_creacion() --
    # coste_empujar (Empujable), volumen (Volumen), rgb_base (Color,
    # necesita un parser tipo tupla propio), temperatura_propia y
    # tasa_transferencia_temperatura (Termico), etc.
}
