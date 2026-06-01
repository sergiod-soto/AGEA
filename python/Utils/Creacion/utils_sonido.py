"""
sonido_inverso.py — Optimización inversa de audio (mono y multi-base)
======================================================================
Dos funciones principales:

    aproximar(ruta, ...)
        → ResultadoAproximacion  (una sola SonidoBase)

    obtencion_parametros_sonido(ruta, max_bases=4, ...)
        → ResultadoMultibases    (lista de SonidoBase, una por fuente)

El algoritmo multi-base:
    1. Detecta picos prominentes en el espectro FFT
    2. Agrupa los que tienen relación armónica (misma fundamental)
       → cada grupo es una fuente física distinta
    3. Ajusta una SonidoBase independiente a cada grupo
    4. Para cuando añadir otra base mejora menos de `umbral_mejora`
    5. Devuelve hasta `max_bases` bases ordenadas por importancia

Uso:
    from sonido_inverso import aproximar, obtencion_parametros_sonido

    # una sola base
    r = aproximar("piedra.wav")
    r.base.build().reproducir()

    # múltiples bases
    r = obtencion_parametros_sonido("piedra.wav", max_bases=3)
    print(r)
    r.fusionado().reproducir()

    # usar las bases en Sonoro
    for base in r.bases:
        print(base)
"""

from __future__ import annotations

import numpy as np
import warnings
from dataclasses import dataclass

import librosa
import scipy.optimize as opt
from scipy.signal import find_peaks

from Core.Entities.Elementos.Abstractos.Informacion.sonido import (
    Sonido,
    SonidoBase,
    SAMPLE_RATE,
    FREQ_MIN,
    FREQ_MAX,
)

# ---------------------------------------------------------------------------
# Carga y espectro
# ---------------------------------------------------------------------------


def _cargar_audio(ruta: str) -> tuple[np.ndarray, float]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        señal, _ = librosa.load(ruta, sr=SAMPLE_RATE, mono=True)
    return señal.astype(np.float64), len(señal) / SAMPLE_RATE


def _espectro(señal: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """FFT normalizada, solo rango audible."""
    n = len(señal)
    esp = np.abs(np.fft.rfft(señal))
    freqs = np.fft.rfftfreq(n, d=1.0 / SAMPLE_RATE)
    mask = (freqs >= FREQ_MIN) & (freqs <= FREQ_MAX)
    freqs = freqs[mask]
    esp = esp[mask]
    mx = esp.max()
    if mx > 1e-9:
        esp /= mx
    return freqs, esp


# ---------------------------------------------------------------------------
# Síntesis rápida (sin overhead de clases, para el optimizador)
# ---------------------------------------------------------------------------


def _sintetizar(
    n: int,
    duracion: float,
    fundamental: float,
    inarmonicidad: float,
    amplitudes: np.ndarray,
    ataque: float,
    sustain: float,
    release: float,
    vol: float,
) -> np.ndarray:
    t = np.linspace(0.0, duracion, n, endpoint=False)
    señal = np.zeros(n, dtype=np.float64)
    for i, amp in enumerate(amplitudes):
        freq = fundamental * (i + 1) * (1.0 + inarmonicidad * i)
        if FREQ_MIN <= freq <= FREQ_MAX:
            señal += amp * np.sin(2.0 * np.pi * freq * t)

    env = np.zeros(n)
    ataque_n = int(n * ataque)
    sustain_n = int(n * sustain)
    release_n = int(n * release)
    if ataque_n > 0:
        env[:ataque_n] = np.linspace(0.0, 1.0, ataque_n)
    if sustain_n > ataque_n:
        env[ataque_n:sustain_n] = 1.0
    if release_n > sustain_n:
        tramo = release_n - sustain_n
        env[sustain_n:release_n] = np.exp(np.linspace(0.0, -5.0, tramo))

    return señal * env * vol


def _espectro_sint(señal: np.ndarray, freqs_ref: np.ndarray) -> np.ndarray:
    n = len(señal)
    esp = np.abs(np.fft.rfft(señal))
    freqs = np.fft.rfftfreq(n, d=1.0 / SAMPLE_RATE)
    out = np.interp(freqs_ref, freqs, esp)
    mx = out.max()
    return out / mx if mx > 1e-9 else out


# ---------------------------------------------------------------------------
# Optimización de una sola base
# ---------------------------------------------------------------------------


def _perdida(params, n_arm, n_muestras, duracion, freqs_ref, esp_ref):
    f0 = params[0]
    inar = params[1]
    amps = params[2 : 2 + n_arm]
    at = params[2 + n_arm]
    su = params[3 + n_arm]
    re = params[4 + n_arm]
    vol = params[5 + n_arm]
    if not (0.0 < at <= su <= re <= 1.0):
        return 1.0
    s = _sintetizar(n_muestras, duracion, f0, inar, amps, at, su, re, vol)
    esp = _espectro_sint(s, freqs_ref)
    return float(np.mean((esp_ref - esp) ** 2))


def _optimizar_base(
    n_arm: int,
    f0_inicial: float,
    n_muestras: int,
    duracion: float,
    freqs_ref: np.ndarray,
    esp_ref: np.ndarray,
) -> tuple[float, np.ndarray]:
    """Optimiza una base con n_arm armónicos. Devuelve (perdida, params)."""
    x0 = np.concatenate(
        [
            [f0_inicial, 0.01],
            [0.8**i for i in range(n_arm)],
            [0.02, 0.05, 0.8, 0.8],
        ]
    )
    bounds = (
        [(FREQ_MIN, FREQ_MAX), (0.0, 0.5)]
        + [(0.0, 1.0)] * n_arm
        + [(0.001, 0.999), (0.001, 0.999), (0.001, 1.0), (0.01, 1.0)]
    )
    res = opt.minimize(
        _perdida,
        x0,
        args=(n_arm, n_muestras, duracion, freqs_ref, esp_ref),
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": 1000, "ftol": 1e-12, "gtol": 1e-8},
    )
    return res.fun, res.x


def _params_a_base(params: np.ndarray, n_arm: int, duracion: float) -> SonidoBase:
    f0 = float(params[0])
    inar = float(params[1])
    amps = params[2 : 2 + n_arm]
    at = float(params[2 + n_arm])
    su = float(params[3 + n_arm])
    re = float(params[4 + n_arm])
    vol = float(params[5 + n_arm])
    at = min(at, su, re)
    su = max(min(su, re), at)

    base = SonidoBase(duracion=duracion)
    for i, amp in enumerate(amps):
        freq = f0 * (i + 1) * (1.0 + inar * i)
        base.agregar(freq, float(amp))
    base.con_vol(vol).con_envolvente(at, su, re)
    return base


# ---------------------------------------------------------------------------
# Detección de grupos armónicos
# ---------------------------------------------------------------------------


def _detectar_grupos(
    freqs_ref: np.ndarray,
    esp_ref: np.ndarray,
    max_grupos: int,
    tolerancia: float = 0.03,
    umbral_altura: float = 0.05,
) -> list[float]:
    """
    Detecta hasta max_grupos fundamentales independientes en el espectro.
    Devuelve lista de frecuencias fundamentales ordenadas por amplitud.
    """
    picos_idx, _ = find_peaks(
        esp_ref,
        height=esp_ref.max() * umbral_altura,
        distance=20,
    )
    if len(picos_idx) == 0:
        return [float(freqs_ref[np.argmax(esp_ref)])]

    picos_freq = freqs_ref[picos_idx]
    picos_amp = esp_ref[picos_idx]

    # Ordenar por amplitud descendente
    orden = np.argsort(picos_amp)[::-1]
    picos_freq = picos_freq[orden]
    picos_amp = picos_amp[orden]

    # Agrupar por relación armónica
    usados = [False] * len(picos_freq)
    fundamentales = []

    for i in range(len(picos_freq)):
        if len(fundamentales) >= max_grupos:
            break
        if usados[i]:
            continue
        f0 = picos_freq[i]
        usados[i] = True
        # marcar como usados los armónicos de esta fundamental
        for j in range(i + 1, len(picos_freq)):
            if usados[j]:
                continue
            ratio = picos_freq[j] / f0
            entero = round(ratio)
            if entero >= 2 and abs(ratio - entero) / entero < tolerancia:
                usados[j] = True
        fundamentales.append(float(f0))

    return fundamentales


# ---------------------------------------------------------------------------
# Resultados
# ---------------------------------------------------------------------------


@dataclass
class ResultadoAproximacion:
    base: SonidoBase
    n_armonicos: int
    fundamental: float
    amplitudes: list[float]
    inarmonicidad: float
    ataque: float
    sustain: float
    release: float
    vol: float
    perdida: float
    duracion: float

    def __repr__(self) -> str:
        calidad = (
            "buena"
            if self.perdida < 0.1
            else "aceptable" if self.perdida < 0.3 else "aproximada"
        )
        return "\n".join(
            [
                "ResultadoAproximacion(",
                f"  fundamental   = {self.fundamental:.2f} Hz",
                f"  n_armonicos   = {self.n_armonicos}",
                f"  inarmonicidad = {self.inarmonicidad:.4f}",
                f"  amplitudes    = {[round(a, 4) for a in self.amplitudes]}",
                f"  envolvente    = ataque={self.ataque:.3f}  sustain={self.sustain:.3f}  release={self.release:.3f}",
                f"  vol           = {self.vol:.4f}",
                f"  duracion      = {self.duracion:.3f} s",
                f"  perdida       = {self.perdida:.6f}  ({calidad})",
                ")",
            ]
        )


@dataclass
class ResultadoMultibases:
    bases: list[SonidoBase]  # una por fuente detectada
    perdidas: list[float]  # pérdida individual de cada base
    perdida_total: float  # error de la fusión completa vs original
    duracion: float
    n_bases: int

    def fusionado(self) -> Sonido:
        """Devuelve el Sonido resultante de fusionar todas las bases."""
        sonidos = [b.build() for b in self.bases]
        resultado = sonidos[0]
        for s in sonidos[1:]:
            resultado = resultado.fusionar(s)
        return resultado

    def __repr__(self) -> str:
        calidad = (
            "buena"
            if self.perdida_total < 0.1
            else "aceptable" if self.perdida_total < 0.3 else "aproximada"
        )
        lineas = [
            f"ResultadoMultibases(n_bases={self.n_bases}, "
            f"perdida_total={self.perdida_total:.6f} ({calidad}))",
        ]
        for i, (base, perdida) in enumerate(zip(self.bases, self.perdidas)):
            lineas.append(f"  Base {i}  perdida={perdida:.6f}")
        return "\n".join(lineas)

    def construir(bases: list[SonidoBase], duracion) -> ResultadoMultibases:
        return ResultadoMultibases(
            bases,
            perdidas_resultado=None,
            perdida_total=None,
            duracion=duracion,
            n_bases=len(bases),
        )


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------


def aproximar(
    ruta: str,
    n_armonicos_min: int = 2,
    n_armonicos_max: int = 12,
    verbose: bool = True,
) -> ResultadoAproximacion:
    """
    Aproxima un fichero de audio con una sola SonidoBase.
    Prueba n_armonicos de min a max y se queda con el mejor.
    """
    if verbose:
        print(f"Cargando '{ruta}'...")

    señal, duracion = _cargar_audio(ruta)
    n_muestras = len(señal)
    freqs_ref, esp_ref = _espectro(señal)
    f0_inicial = float(freqs_ref[np.argmax(esp_ref[: len(esp_ref) // 2])])

    if verbose:
        print(
            f"Duración: {duracion:.3f}s  |  Fundamental estimada: {f0_inicial:.1f} Hz"
        )
        print(f"Probando n_armonicos de {n_armonicos_min} a {n_armonicos_max}...\n")

    mejor_perdida = np.inf
    mejor_params = None
    mejor_n = n_armonicos_min

    for n_arm in range(n_armonicos_min, n_armonicos_max + 1):
        perdida, params = _optimizar_base(
            n_arm, f0_inicial, n_muestras, duracion, freqs_ref, esp_ref
        )
        if verbose:
            estado = "✓" if perdida < mejor_perdida else " "
            print(f"  [{estado}] n_armonicos={n_arm:2d}  pérdida={perdida:.6f}")
        if perdida < mejor_perdida:
            mejor_perdida = perdida
            mejor_params = params
            mejor_n = n_arm

    base = _params_a_base(mejor_params, mejor_n, duracion)

    if verbose:
        print()

    return ResultadoAproximacion(
        base=base,
        n_armonicos=mejor_n,
        fundamental=float(mejor_params[0]),
        amplitudes=list(mejor_params[2 : 2 + mejor_n]),
        inarmonicidad=float(mejor_params[1]),
        ataque=float(mejor_params[2 + mejor_n]),
        sustain=float(mejor_params[3 + mejor_n]),
        release=float(mejor_params[4 + mejor_n]),
        vol=float(mejor_params[5 + mejor_n]),
        perdida=mejor_perdida,
        duracion=duracion,
    )


def obtencion_parametros_sonido(
    ruta: str,
    max_bases: int = 4,
    n_armonicos_min: int = 2,
    n_armonicos_max: int = 8,
    umbral_mejora: float = 0.005,
    verbose: bool = True,
) -> ResultadoMultibases:
    """
    Aproxima un fichero de audio con múltiples SonidoBase independientes.
    Cada base corresponde a una fuente física distinta (fundamental distinta).

    Parámetros:
        max_bases       : número máximo de bases a usar
        n_armonicos_min : mínimo de armónicos por base
        n_armonicos_max : máximo de armónicos por base
        umbral_mejora   : si añadir una base mejora menos que esto, para
        verbose         : imprime progreso
    """
    if verbose:
        print(f"Cargando '{ruta}'...")

    señal, duracion = _cargar_audio(ruta)
    n_muestras = len(señal)
    freqs_ref, esp_ref = _espectro(señal)

    if verbose:
        print(f"Duración: {duracion:.3f}s")
        print(f"Detectando fuentes (max_bases={max_bases})...\n")

    # Detectar fundamentales candidatas
    fundamentales = _detectar_grupos(freqs_ref, esp_ref, max_grupos=max_bases)

    if verbose:
        print(f"  Fundamentales detectadas: {[f'{f:.1f}Hz' for f in fundamentales]}\n")

    bases_resultado = []
    perdidas_resultado = []
    esp_residual = esp_ref.copy()  # espectro que queda por explicar
    perdida_anterior = float(np.mean(esp_residual**2))

    for idx, f0 in enumerate(fundamentales):
        if verbose:
            print(f"── Base {idx}  (fundamental≈{f0:.1f} Hz) ──")

        # Encontrar mejor n_armonicos para esta base sobre el residual
        mejor_perdida_base = np.inf
        mejor_params_base = None
        mejor_n_base = n_armonicos_min

        for n_arm in range(n_armonicos_min, n_armonicos_max + 1):
            perdida, params = _optimizar_base(
                n_arm,
                f0,
                n_muestras,
                duracion,
                freqs_ref,
                esp_residual,
            )
            if verbose:
                estado = "✓" if perdida < mejor_perdida_base else " "
                print(f"  [{estado}] n_armonicos={n_arm:2d}  pérdida={perdida:.6f}")
            if perdida < mejor_perdida_base:
                mejor_perdida_base = perdida
                mejor_params_base = params
                mejor_n_base = n_arm

        # Calcular espectro de esta base y restar del residual
        señal_base = _sintetizar(
            n_muestras,
            duracion,
            float(mejor_params_base[0]),
            float(mejor_params_base[1]),
            mejor_params_base[2 : 2 + mejor_n_base],
            float(mejor_params_base[2 + mejor_n_base]),
            float(mejor_params_base[3 + mejor_n_base]),
            float(mejor_params_base[4 + mejor_n_base]),
            float(mejor_params_base[5 + mejor_n_base]),
        )
        esp_base = _espectro_sint(señal_base, freqs_ref)
        esp_residual = np.maximum(0.0, esp_residual - esp_base)

        perdida_nueva = float(np.mean(esp_residual**2))
        mejora = perdida_anterior - perdida_nueva

        if verbose:
            print(f"  → mejora={mejora:.6f}  residual={perdida_nueva:.6f}\n")

        bases_resultado.append(
            _params_a_base(mejor_params_base, mejor_n_base, duracion)
        )
        perdidas_resultado.append(mejor_perdida_base)
        perdida_anterior = perdida_nueva

        # Parar si la mejora es insignificante
        if mejora < umbral_mejora and idx > 0:
            if verbose:
                print(
                    f"  Mejora < umbral ({umbral_mejora}), parando en {idx + 1} bases.\n"
                )
            break

    # Calcular pérdida total de la fusión
    sonidos = [b.build() for b in bases_resultado]
    fusionado = sonidos[0]
    for s in sonidos[1:]:
        fusionado = fusionado.fusionar(s)
    esp_fusion = _espectro_sint(fusionado._señal_raw, freqs_ref)
    perdida_total = float(np.mean((esp_ref - esp_fusion) ** 2))

    if verbose:
        print(f"Pérdida total de la fusión: {perdida_total:.6f}")

    return ResultadoMultibases(
        bases=bases_resultado,
        perdidas=perdidas_resultado,
        perdida_total=perdida_total,
        duracion=duracion,
        n_bases=len(bases_resultado),
    )
                                                            