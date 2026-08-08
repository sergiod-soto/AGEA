# tests/Entities/Elementos/test_sonido.py

from Core.Entities.Elementos.Abstractos.Informacion.sonido import SonidoBase
from Services.Elemento.cache_audio import CacheAudio


def _sonido_simple(duracion=0.1, freq=440.0, amp=1.0):
    return SonidoBase.generar_frecuencia(duracion, freq, [amp]).build()


class TestIdSonido:
    def test_dos_sonidos_con_mismo_contenido_comparten_id(self):
        # mismo duracion/fundamental/amplitudes -> mismo pcm -> mismo id,
        # sin haberlo coordinado a mano (simula dos Piedras con igual peso)
        s1 = _sonido_simple()
        s2 = _sonido_simple()
        assert s1.id_sonido == s2.id_sonido
        assert s1 is not s2  # pero son objetos distintos, como se pidio

    def test_sonidos_con_distinto_contenido_tienen_distinto_id(self):
        s1 = _sonido_simple(freq=440.0)
        s2 = _sonido_simple(freq=220.0)
        assert s1.id_sonido != s2.id_sonido

    def test_id_es_estable_para_la_misma_instancia(self):
        s = _sonido_simple()
        assert s.id_sonido == s.id_sonido


class TestSerializacionEnDosNiveles:
    def test_referencia_no_incluye_audio(self):
        s = _sonido_simple()
        ref = s.serializar_referencia()
        assert set(ref.keys()) == {"id", "duracion", "vol"}
        assert "vector" not in ref
        assert "pcm" not in ref

    def test_referencia_es_json_serializable(self):
        import json

        s = _sonido_simple()
        json.dumps(s.serializar_referencia())  # no debe lanzar

    def test_audio_completo_incluye_vector_y_pcm_como_listas(self):
        s = _sonido_simple()
        audio = s.serializar_audio()
        assert isinstance(audio["vector"], list)
        assert isinstance(audio["pcm"], list)
        assert audio["id"] == s.id_sonido

    def test_audio_completo_es_json_serializable(self):
        import json

        s = _sonido_simple()
        json.dumps(s.serializar_audio())  # no debe lanzar


class TestCacheAudio:
    def test_registrar_y_obtener(self):
        cache = CacheAudio()
        s = _sonido_simple()
        cache.registrar(s)
        assert cache.obtener(s.id_sonido) == s.serializar_audio()

    def test_registrar_dos_veces_mismo_contenido_no_duplica(self):
        cache = CacheAudio()
        s1 = _sonido_simple()
        s2 = _sonido_simple()  # mismo contenido, objeto distinto
        cache.registrar(s1)
        cache.registrar(s2)
        assert len(cache._audios) == 1  # una sola entrada, no dos

    def test_tiene(self):
        cache = CacheAudio()
        s = _sonido_simple()
        assert cache.tiene(s.id_sonido) is False
        cache.registrar(s)
        assert cache.tiene(s.id_sonido) is True

    def test_obtener_id_no_registrado_lanza_keyerror(self):
        import pytest

        cache = CacheAudio()
        with pytest.raises(KeyError):
            cache.obtener("id-que-no-existe")
