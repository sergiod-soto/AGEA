import numpy as np
import sounddevice as sd

from Core.Entities.Comportamiento.Informativo.sonoro import Sonoro
from Core.Entities.Elementos.Simples.Piedra.piedra import Piedra

SAMPLE_RATE = 44100


def sintetizar(parciales, duracion=2.0):
    t = np.linspace(0, duracion, int(SAMPLE_RATE * duracion), False)

    señal = np.zeros_like(t)

    for freq, amp in parciales:
        señal += amp * np.sin(2 * np.pi * freq * t)

    # normalizar para evitar clipping
    max_val = np.max(np.abs(señal))
    if max_val > 0:
        señal /= max_val

    return señal.astype(np.float32)


def reproducir(parciales, duracion=1.0):
    audio = sintetizar(parciales, duracion)
    sd.play(audio, SAMPLE_RATE)
    sd.wait()


piedra = Piedra(
    1,
    (0, 0),
    0,
    10.0,
    0.0,
    0.0,
    None,
    (0, 0, 0),
    None,
    0.0,
    0.0,
    0.0,
    0.0,
    None,
    0.0,
)

reproducir(piedra.sonidos["GOLPEAR"][0])
