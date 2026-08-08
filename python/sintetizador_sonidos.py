from Core.Entities.Elementos.Simples.Piedra.piedra import Piedra

piedra = Piedra(
    tamanho=1,
    id_elemento=0,
    rgb_base=(0, 0, 0),
    casilla=(0, 0),
    tasa_transferencia_temperatura=0,
    capa=0,
    peso=1000.0,
    coste_empujar=0.0,
    volumen=0.0,
    agarrado_por=None,
    durabilidad_max=0.0,
    temperatura_propia=0.0,
    radio_termico=0.0,
    durabilidad_actual=None,
    durabilidad_actual_erosion=None,
    rotacion=0,
)

audio = piedra.sonidos["GOLPEAR"][0]

from Utils.Creacion.utils_sonido import obtencion_parametros_sonido

#
#
#
escuchar = True
if escuchar:
    audio.reproducir()
    print("vector, len: " + str(len(audio.vector)))
    print(audio.vector)
else:
    resultado = obtencion_parametros_sonido(
        "D:\\Descargas\\spinopel-stone-strikes-321447 (mp3cut.net).mp3", max_bases=4
    )
    print(resultado)  # ver todos los parámetros
    resultado.fusionado().reproducir()  # escuchar la aproximación
    print("_" * 20)
    for i, base in enumerate(resultado.bases):
        print(f"Base {i}:", base.__repr__())
