"""
sonido.py
=========
Dos clases:

    SonidoBase  — construcción armónico a armónico. mutable.
                  .build() → Sonido

    Sonido      — inmutable. dos representaciones del mismo sonido:
                  .vector  → np.ndarray (N_BANDAS,)   para la IA
                  .pcm     → np.ndarray (n_muestras,) para audio (float32, [-1, 1])

Constantes configurables:
    SAMPLE_RATE  : muestras por segundo (default 44100)
    N_BANDAS     : tamaño del vector FFT que recibe la IA (default 256)
    FREQ_MIN/MAX : rango audible en Hz (20 – 20000)

Reproducción:
    Python → sonido.reproducir()          requiere: pip install sounddevice
    Unity  → sonido.pcm y sonido.SAMPLE_RATE
              AudioClip.SetData(float[], int) acepta float32 directamente
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass

from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto

# ---------------------------------------------------------------------------
# Constantes del sistema — modificar aquí afecta a todo
# ---------------------------------------------------------------------------

SAMPLE_RATE: int = 44_100
N_BANDAS: int = 256
FREQ_MIN: float = 20.0
FREQ_MAX: float = 20_000.0


# ---------------------------------------------------------------------------
# Armonico — par de floats, sin lógica
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Armonico:
    freq: float  # Hz
    amp: float  # amplitud relativa [0, ∞)


# ---------------------------------------------------------------------------
# SonidoBase — construcción, mutable
# ---------------------------------------------------------------------------


class SonidoBase(Elemento_Abstracto):
    """
    Construye un sonido armónico a armónico antes de "sellarlo" con build().

    Ejemplo:
        base = SonidoBase(duracion=0.5)
        base.agregar(440.0, 1.0)
        base.agregar(880.0, 0.5)
        base.con_vol(0.8)
        base.con_envolvente(ataque=0.01, decay=0.99)
        sonido = base.build()

    """

    def __init__(self, duracion: float, **kwargs):
        """
        duracion : duración en segundos de la ventana de sonido.
                   determina la longitud del PCM y la resolución de la FFT.
        """
        self.duracion: float = duracion
        self._armonicos: list[Armonico] = []
        self._vol: float = 1.0
        self._ataque: float | None = None
        self._decay: float | None = None

        super().__init__(SonidoBase, **kwargs)

    def __repr__(self) -> str:
        lineas = [
            f"SonidoBase(",
            f"  duracion      = {self.duracion:.3f} s",
            f"  vol           = {self._vol:.4f}",
        ]

        if self._ataque is not None:
            lineas.append(
                f"  envolvente    = ataque={self._ataque:.3f}  "
                f"sustain={self._sustain:.3f}  release={self._release:.3f}"
            )
        else:
            lineas.append(f"  envolvente    = ninguna")

        lineas.append(f"  armonicos     = {len(self._armonicos)}")
        for a in self._armonicos:
            audible = "✓" if FREQ_MIN <= a.freq <= FREQ_MAX else "✗ inaudible"
            lineas.append(f"    {a.freq:>10.2f} Hz  amp={a.amp:.4f}  {audible}")

        lineas.append(")")
        return "\n".join(lineas)

    def agregar(self, freq: float, amp: float) -> "SonidoBase":
        self._armonicos.append(Armonico(freq, amp))
        return self

    def con_vol(self, vol: float) -> "SonidoBase":
        self._vol = vol
        return self

    @staticmethod
    def fusionar(*bases: "SonidoBase") -> "Sonido":
        sonidos = [b.build() for b in bases]
        resultado = sonidos[0]
        for s in sonidos[1:]:
            resultado = resultado.fusionar(s)
        return resultado

    @staticmethod
    def generar_frecuencia(
        duracion: float,
        fundamental: float,
        amplitudes: list[float],
    ) -> "SonidoBase":
        base = SonidoBase(duracion=duracion)
        for i, amp in enumerate(amplitudes):
            freq = fundamental * (i + 1)
            base.agregar(freq, amp)
        return base

    def con_envolvente(
        self,
        ataque: float = 0.01,
        sustain: float = 0.01,
        release: float = 1.0,
    ) -> "SonidoBase":
        """
        Envolvente de tres fases sobre la duración total del sonido.
        Los tres parámetros son puntos en [0, 1] (fracción de la duración):

            0.0 → ataque  : sube linealmente de 0 a 1
            ataque → sustain : se mantiene a 1
            sustain → release : cae exponencialmente (como en la realidad)
            release → 1.0 : silencio

        Ejemplos:
            golpe seco    → ataque=0.01, sustain=0.01, release=1.0
            golpe con eco → ataque=0.01, sustain=0.30, release=1.0
            tu ejemplo    → ataque=0.4,  sustain=0.6,  release=1.0
            pad suave     → ataque=0.3,  sustain=0.7,  release=1.0
        """

        self._ataque = ataque
        self._sustain = sustain
        self._release = release
        return self

    def build(self) -> "Sonido":
        """
        Sintetiza y devuelve un Sonido inmutable.
        Armónicos fuera de [FREQ_MIN, FREQ_MAX] se ignoran.
        """
        audibles = [a for a in self._armonicos if FREQ_MIN <= a.freq <= FREQ_MAX]

        n = int(SAMPLE_RATE * self.duracion)
        t = np.linspace(0.0, self.duracion, n, endpoint=False)

        señal = np.zeros(n, dtype=np.float64)
        for a in audibles:
            señal += (a.amp * self._vol) * np.sin(2.0 * np.pi * a.freq * t)

        if self._ataque is not None:
            señal *= _envolvente(n, self._ataque, self._sustain, self._release)

        pcm = _normalizar(señal).astype(np.float32)
        vector = _fft_bandas(señal, n)

        return Sonido(
            vector=vector,
            pcm=pcm,
            duracion=self.duracion,
            vol=self._vol,
            _señal_raw=señal,
        )


# ---------------------------------------------------------------------------
# Sonido — inmutable
# ---------------------------------------------------------------------------


class Sonido(Elemento_Abstracto):
    """
    Sonido inmutable con dos representaciones:

        .vector  → np.ndarray (N_BANDAS,)   amplitudes por banda de frecuencia
        .pcm     → np.ndarray (n_muestras,) float32 en [-1, 1], listo para audio

    Operaciones que devuelven un nuevo Sonido:
        .fusionar(otro)  → suma física de señales (comportamiento real)
        .con_vol(v)      → escala el volumen

    Reproducción:
        .reproducir()    → reproduce en Python (requiere sounddevice)
        .SAMPLE_RATE     → constante necesaria para Unity
    """

    SAMPLE_RATE = SAMPLE_RATE

    def __init__(
        self,
        vector: np.ndarray,
        pcm: np.ndarray,
        duracion: float,
        vol: float,
        _señal_raw: np.ndarray,  # señal sin normalizar, para fusionar
        **kwargs,
    ):
        super().__init__(Sonido, **kwargs)
        self.vector: np.ndarray = vector
        self.pcm: np.ndarray = pcm
        self.duracion: float = duracion
        self.vol: float = vol
        self._señal_raw = _señal_raw

    # ------------------------------------------------------------------
    # Operaciones
    # ------------------------------------------------------------------

    def fusionar(self, otro: "Sonido") -> "Sonido":
        """
        Suma física de dos señales — igual que en la realidad.
        Si tienen distinta duración, la más corta se rellena con silencio.
        La duración del resultado es la mayor de las dos.
        """
        a, b = _igualar_longitud(self._señal_raw, otro._señal_raw)
        señal = a + b
        dur = max(self.duracion, otro.duracion)
        n = len(señal)

        pcm = _normalizar(señal).astype(np.float32)
        vector = _fft_bandas(señal, n)

        return Sonido(
            vector=vector,
            pcm=pcm,
            duracion=dur,
            vol=max(self.vol, otro.vol),
            _señal_raw=señal,
        )

    def con_vol(self, vol: float) -> "Sonido":
        """Devuelve una copia escalada al nuevo volumen."""
        factor = vol / self.vol if self.vol != 0.0 else 0.0
        señal = self._señal_raw * factor
        n = len(señal)

        pcm = _normalizar(señal).astype(np.float32)
        vector = _fft_bandas(señal, n)

        return Sonido(
            vector=vector,
            pcm=pcm,
            duracion=self.duracion,
            vol=vol,
            _señal_raw=señal,
        )

    # ------------------------------------------------------------------
    # Reproducción
    # ------------------------------------------------------------------

    def reproducir(self) -> None:
        """
        Reproduce el sonido en tiempo real en Python.
        Requiere: pip install sounddevice
        No crea ningún fichero intermedio.
        """
        try:
            import sounddevice as sd

            sd.play(self.pcm, samplerate=SAMPLE_RATE)
            sd.wait()
        except ImportError:
            raise ImportError(
                "reproducir() requiere sounddevice: pip install sounddevice"
            )

    # ------------------------------------------------------------------
    # Representación
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Sonido(dur={self.duracion:.3f}s, vol={self.vol:.3f}, "
            f"vector={self.vector.shape}, pcm={self.pcm.shape})"
        )


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------


def _envolvente(n: int, ataque: float, sustain: float, release: float) -> np.ndarray:
    """
    Envolvente de tres fases. ataque, sustain, release son puntos en [0, 1].
      0       → ataque  : sube linealmente de 0 a 1
      ataque  → sustain : se mantiene a 1
      sustain → release : cae exponencialmente (física real)
      release → 1       : silencio
    """
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

    return env


def _normalizar(señal: np.ndarray) -> np.ndarray:
    """Escala la señal a [-1, 1]. Si es silencio, devuelve ceros."""
    mx = np.max(np.abs(señal))
    return señal / mx if mx > 1e-9 else np.zeros_like(señal)


def _fft_bandas(señal: np.ndarray, n: int) -> np.ndarray:
    """
    FFT → vector de N_BANDAS amplitudes en bandas lineales [FREQ_MIN, FREQ_MAX].
    Armónicos fuera del rango no contribuyen al vector.
    """
    espectro = np.abs(np.fft.rfft(señal))
    freqs = np.fft.rfftfreq(n, d=1.0 / SAMPLE_RATE)
    ancho = (FREQ_MAX - FREQ_MIN) / N_BANDAS

    vector = np.zeros(N_BANDAS, dtype=np.float32)
    for i in range(N_BANDAS):
        lo = FREQ_MIN + i * ancho
        hi = lo + ancho
        mask = (freqs >= lo) & (freqs < hi)
        if mask.any():
            vector[i] = float(espectro[mask].sum())

    return vector


def _igualar_longitud(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Rellena con ceros la señal más corta hasta igualar longitudes."""
    if len(a) == len(b):
        return a, b
    n = max(len(a), len(b))
    return (
        np.pad(a, (0, n - len(a))),
        np.pad(b, (0, n - len(b))),
    )
