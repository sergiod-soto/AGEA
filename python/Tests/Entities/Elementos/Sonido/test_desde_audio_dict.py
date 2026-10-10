# Tests/Entities/Elementos/Sonido/test_desde_audio_dict.py


"""
Tests de Sonido.desde_audio_dict -- reconstrucción de un Sonido real a
partir del payload de serializar_audio(), usado por
Sonoro.deserializar_sonidos al reconstruir un elemento en modo
"guardado"/"transporte".
"""

import numpy as np
import pytest

from Core.Entities.Elementos.Abstractos.Informacion.sonido import SonidoBase, Sonido


def _sonido_simple(freq=440.0):
    return SonidoBase.generar_frecuencia(0.1, freq, [1.0]).build()


class TestDesdeAudioDict:
    def test_id_sonido_coincide_con_el_original(self):
        original = _sonido_simple()
        payload = original.serializar_audio()
        reconstruido = Sonido.desde_audio_dict(payload)
        assert reconstruido.id_sonido == original.id_sonido

    def test_vector_y_pcm_coinciden(self):
        original = _sonido_simple()
        payload = original.serializar_audio()
        reconstruido = Sonido.desde_audio_dict(payload)
        assert np.allclose(reconstruido.pcm, original.pcm)
        assert np.allclose(reconstruido.vector, original.vector)

    def test_duracion_y_vol_coinciden(self):
        original = _sonido_simple()
        payload = original.serializar_audio()
        reconstruido = Sonido.desde_audio_dict(payload)
        assert reconstruido.duracion == original.duracion
        assert reconstruido.vol == original.vol

    def test_id_corrupto_en_el_payload_lanza_valueerror(self):
        # Comprobación defensiva: si el id que trae el payload no coincide
        # con el que se recalcula del pcm, algo se corrompió en el camino
        # -- mejor fallar aquí que servir audio con el id equivocado.
        original = _sonido_simple()
        payload = original.serializar_audio()
        payload["id"] = "id-corrupto-a-mano"
        with pytest.raises(ValueError):
            Sonido.desde_audio_dict(payload)
