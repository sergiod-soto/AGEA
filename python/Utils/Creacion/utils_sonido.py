"""
sonido_inverso.py — Optimización inversa de audio
==================================================
Dada una pista de audio (.wav o .mp3), encuentra los parámetros de
SonidoBase que mejor aproximan ese sonido.

Parámetros que se optimizan:
    - fundamental      : frecuencia base en Hz
    - inarmonicidad    : desviación de cada armónico respecto al múltiplo exacto
    - amplitudes       : amplitud individual de cada armónico
    - ataque           : punto de fin del ataque  [0, 1]
    - sustain          : punto de fin del sustain [0, 1]
    - release          : punto de fin del release [0, 1]
    - vol              : volumen global

El proceso:
    1. Cargar el audio y calcular su espectro FFT de referencia
    2. Para cada n_armonicos en el rango dado, optimizar con L-BFGS-B
    3. Quedarse con el n_armonicos que da menor pérdida espectral
    4. Devolver un SonidoBase listo para usar + métricas

Uso:
    from sonido_inverso import aproximar

    resultado = aproximar("golpe_piedra.wav")
    print(resultado)
    resultado.base.build().reproducir()
"""

from __future__ import annotations

import numpy as np
import warnings
from dataclasses import dataclass
from Core.Entities.Elementos.Abstractos.Informacion.sonido import SonidoBase, SAMPLE_RATE, FREQ_MIN, FREQ_MAX


import librosa
import scipy.optimize as opt



# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------

@dataclass
class ResultadoAproximacion:
    base:          SonidoBase   # listo para .build()
    n_armonicos:   int
    fundamental:   float        # Hz
    amplitudes:    list[float]
    inarmonicidad: float
    ataque:        float
    sustain:       float
    release:       float
    vol:           float
    perdida:       float        # error espectral normalizado [0, 1]
    duracion:      float        # segundos

    def __repr__(self) -> str:
        lineas = [
            f"ResultadoAproximacion(",
            f"  fundamental   = {self.fundamental:.2f} Hz",
            f"  n_armonicos   = {self.n_armonicos}",
            f"  inarmonicidad = {self.inarmonicidad:.4f}",
            f"  amplitudes    = {[round(a, 4) for a in self.amplitudes]}",
            f"  envolvente    = ataque={self.ataque:.3f}  "
                               f"sustain={self.sustain:.3f}  "
                               f"release={self.release:.3f}",
            f"  vol           = {self.vol:.4f}",
            f"  duracion      = {self.duracion:.3f} s",
            f"  perdida       = {self.perdida:.6f}  "
                               f"({'buena' if self.perdida < 0.1 else 'aceptable' if self.perdida < 0.3 else 'aproximada'})",
            f")",
        ]
        return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Carga de audio
# ---------------------------------------------------------------------------

def _cargar_audio(ruta: str) -> tuple[np.ndarray, float]:
    """
    Carga un fichero .wav o .mp3.
    Devuelve (señal_mono_float32, duracion_segundos).
    Remuestrea a SAMPLE_RATE si es necesario.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        señal, sr = librosa.load(ruta, sr=SAMPLE_RATE, mono=True)

    duracion = len(señal) / SAMPLE_RATE
    return señal.astype(np.float64), duracion


# ---------------------------------------------------------------------------
# Espectro de referencia
# ---------------------------------------------------------------------------

def _espectro_referencia(señal: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Calcula el espectro de amplitud del audio objetivo.
    Solo conserva el rango audible [FREQ_MIN, FREQ_MAX].
    Normaliza a [0, 1].
    """
    n        = len(señal)
    espectro = np.abs(np.fft.rfft(señal))
    freqs    = np.fft.rfftfreq(n, d=1.0 / SAMPLE_RATE)

    mask     = (freqs >= FREQ_MIN) & (freqs <= FREQ_MAX)
    freqs    = freqs[mask]
    espectro = espectro[mask]

    mx = espectro.max()
    if mx > 1e-9:
        espectro /= mx

    return freqs, espectro


# ---------------------------------------------------------------------------
# Síntesis rápida para el optimizador (sin crear objetos Sonido)
# ---------------------------------------------------------------------------

def _sintetizar_rapido(
    n:             int,
    duracion:      float,
    fundamental:   float,
    inarmonicidad: float,
    amplitudes:    np.ndarray,
    ataque:        float,
    sustain:       float,
    release:       float,
    vol:           float,
) -> np.ndarray:
    """Síntesis directa en numpy, sin overhead de clases."""
    t     = np.linspace(0.0, duracion, n, endpoint=False)
    señal = np.zeros(n, dtype=np.float64)

    n_arm = len(amplitudes)
    for i in range(n_arm):
        freq = fundamental * (i + 1) * (1.0 + inarmonicidad * i)
        if FREQ_MIN <= freq <= FREQ_MAX:
            señal += amplitudes[i] * np.sin(2.0 * np.pi * freq * t)

    # envolvente
    env       = np.zeros(n)
    ataque_n  = int(n * ataque)
    sustain_n = int(n * sustain)
    release_n = int(n * release)

    if ataque_n > 0:
        env[:ataque_n] = np.linspace(0.0, 1.0, ataque_n)
    if sustain_n > ataque_n:
        env[ataque_n:sustain_n] = 1.0
    if release_n > sustain_n:
        tramo = release_n - sustain_n
        env[sustain_n:release_n] = np.exp(np.linspace(0.0, -5.0, tramo))

    señal *= env * vol
    return señal


def _espectro_sintetizado(
    señal: np.ndarray,
    freqs_ref: np.ndarray,
    n_total: int,
) -> np.ndarray:
    """FFT de la señal sintetizada, interpolada a las mismas frecuencias de referencia."""
    espectro = np.abs(np.fft.rfft(señal))
    freqs    = np.fft.rfftfreq(n_total, d=1.0 / SAMPLE_RATE)

    # Interpolar al grid de frecuencias de referencia
    espectro_interp = np.interp(freqs_ref, freqs, espectro)

    mx = espectro_interp.max()
    if mx > 1e-9:
        espectro_interp /= mx

    return espectro_interp


# ---------------------------------------------------------------------------
# Función de pérdida
# ---------------------------------------------------------------------------

def _perdida(
    params:        np.ndarray,
    n_armonicos:   int,
    n_muestras:    int,
    duracion:      float,
    freqs_ref:     np.ndarray,
    espectro_ref:  np.ndarray,
) -> float:
    """
    Error cuadrático medio entre espectro objetivo y sintetizado.
    params = [fundamental, inarmonicidad, amp_0..amp_n, ataque, sustain, release, vol]
    """
    fundamental   = params[0]
    inarmonicidad = params[1]
    amplitudes    = params[2:2 + n_armonicos]
    ataque        = params[2 + n_armonicos]
    sustain       = params[3 + n_armonicos]
    release       = params[4 + n_armonicos]
    vol           = params[5 + n_armonicos]

    # restricciones de orden (ataque ≤ sustain ≤ release)
    if not (0.0 < ataque <= sustain <= release <= 1.0):
        return 1.0

    señal = _sintetizar_rapido(
        n_muestras, duracion, fundamental, inarmonicidad,
        amplitudes, ataque, sustain, release, vol,
    )

    espectro_sint = _espectro_sintetizado(señal, freqs_ref, n_muestras)
    return float(np.mean((espectro_ref - espectro_sint) ** 2))


# ---------------------------------------------------------------------------
# Estimación inicial inteligente
# ---------------------------------------------------------------------------

def _estimar_fundamental(freqs_ref: np.ndarray, espectro_ref: np.ndarray) -> float:
    """
    Estima la fundamental buscando el pico de mayor amplitud
    en la mitad inferior del espectro.
    """
    mitad = len(freqs_ref) // 2
    idx   = np.argmax(espectro_ref[:mitad])
    return float(freqs_ref[idx])


def _params_iniciales(
    n_armonicos:  int,
    freqs_ref:    np.ndarray,
    espectro_ref: np.ndarray,
) -> np.ndarray:
    """
    Punto de partida para el optimizador.
    [fundamental, inarmonicidad, amp_0..n, ataque, sustain, release, vol]
    """
    fundamental   = _estimar_fundamental(freqs_ref, espectro_ref)
    inarmonicidad = 0.01
    amplitudes    = np.array([0.8 ** i for i in range(n_armonicos)])
    ataque        = 0.02
    sustain       = 0.05
    release       = 0.8
    vol           = 0.8

    return np.concatenate([
        [fundamental, inarmonicidad],
        amplitudes,
        [ataque, sustain, release, vol],
    ])


def _bounds(n_armonicos: int) -> list[tuple[float, float]]:
    """Límites por parámetro para L-BFGS-B."""
    return (
        [(FREQ_MIN, FREQ_MAX)]          # fundamental
        + [(0.0, 0.5)]                  # inarmonicidad
        + [(0.0, 1.0)] * n_armonicos    # amplitudes
        + [(0.001, 0.999)]              # ataque
        + [(0.001, 0.999)]              # sustain
        + [(0.001, 1.000)]              # release
        + [(0.01,  1.000)]              # vol
    )


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def obtencion_parametros(
    ruta:           str,
    n_armonicos_min: int = 1,
    n_armonicos_max: int = 10,
    verbose:        bool = True,
) -> ResultadoAproximacion:
    """
    Aproxima un fichero de audio (.wav o .mp3) con SonidoBase.

    Parámetros:
        ruta            : ruta al fichero de audio
        n_armonicos_min : mínimo de armónicos a probar (default 2)
        n_armonicos_max : máximo de armónicos a probar (default 12)
        verbose         : imprime progreso por pantalla

    Devuelve:
        ResultadoAproximacion con el mejor ajuste encontrado
    """
    if verbose:
        print(f"Cargando '{ruta}'...")

    señal, duracion = _cargar_audio(ruta)
    n_muestras      = len(señal)
    freqs_ref, espectro_ref = _espectro_referencia(señal)

    if verbose:
        print(f"Duración: {duracion:.3f}s  |  Muestras: {n_muestras}  |  "
              f"Bandas espectrales: {len(freqs_ref)}")
        print(f"Probando n_armonicos de {n_armonicos_min} a {n_armonicos_max}...\n")

    mejor_resultado = None
    mejor_perdida   = np.inf

    for n_arm in range(n_armonicos_min, n_armonicos_max + 1):

        x0     = _params_iniciales(n_arm, freqs_ref, espectro_ref)
        bounds = _bounds(n_arm)

        resultado_opt = opt.minimize(
            _perdida,
            x0,
            args=(n_arm, n_muestras, duracion, freqs_ref, espectro_ref),
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 1000, "ftol": 1e-12, "gtol": 1e-8},
        )

        perdida = resultado_opt.fun

        if verbose:
            estado = "✓" if perdida < mejor_perdida else " "
            print(f"  [{estado}] n_armonicos={n_arm:2d}  pérdida={perdida:.6f}")

        if perdida < mejor_perdida:
            mejor_perdida   = perdida
            mejor_resultado = (n_arm, resultado_opt.x)

    n_arm, params = mejor_resultado

    # Extraer parámetros finales
    fundamental   = float(params[0])
    inarmonicidad = float(params[1])
    amplitudes    = list(params[2:2 + n_arm])
    ataque        = float(params[2 + n_arm])
    sustain       = float(params[3 + n_arm])
    release       = float(params[4 + n_arm])
    vol           = float(params[5 + n_arm])

    # Asegurar orden ataque ≤ sustain ≤ release
    ataque  = min(ataque, sustain, release)
    sustain = min(sustain, release)
    sustain = max(sustain, ataque)

    # Construir SonidoBase con los parámetros encontrados
    base = SonidoBase(duracion=duracion)
    for i, amp in enumerate(amplitudes):
        freq = fundamental * (i + 1) * (1.0 + inarmonicidad * i)
        base.agregar(freq, amp)
    base.con_vol(vol).con_envolvente(ataque=ataque, sustain=sustain, release=release)

    if verbose:
        print()

    return ResultadoAproximacion(
        base=base,
        n_armonicos=n_arm,
        fundamental=fundamental,
        amplitudes=amplitudes,
        inarmonicidad=inarmonicidad,
        ataque=ataque,
        sustain=sustain,
        release=release,
        vol=vol,
        perdida=mejor_perdida,
        duracion=duracion,
    )
