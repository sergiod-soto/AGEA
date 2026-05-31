import numpy as np
import sounddevice as sd

from Core.Entities.Comportamiento.Informativo.sonoro import Sonoro
from Core.Entities.Elementos.Simples.Piedra.piedra import Piedra

piedra = Piedra(
    tamanho=1,
    casilla=(0, 0),
    capa=0,
    peso=1.0,
    coste_empujar=0.0,
    volumen=0.0,
    recetas_de=None,
    rgb_color=(0, 0, 0),
    agarrado_por=None,
    durabilidad_max=0.0,
    temperatura_propia=0.0,
    tasa_transferencia=0.0,
    radio_termico=0.0,
    condiciones_erosion=None,
    durabilidad_max_erosion=0.0,
    durabilidad_actual=None,
    durabilidad_actual_erosion=None,
    rotacion=0,
    fuerza_sector_activo=False,
    fuerza_vecinos_activos=False,
)

audio = piedra.sonidos["GOLPEAR"][0]

from Utils.Creacion.utils_sonido import obtencion_parametros

#
#
#
escuchar = False
if escuchar:
    audio.reproducir()
else:
    resultado = obtencion_parametros(
        "D:\\Descargas\\spinopel-stone-strikes-321447 (mp3cut.net).mp3"
    )  # o .wav
    print(resultado)  # ver todos los parámetros
    resultado.base.build().reproducir()  # escuchar la aproximación
