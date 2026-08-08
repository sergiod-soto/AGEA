# Tests/Entities/Elementos/test_biblioteca_sonidos.py
"""
Tests de guardar_en_biblioteca()/liberar_de_biblioteca() en Sonido y del
conteo de referencias en CacheAudio -- el caso concreto que motivó el
contador: dos sonidos con mismo contenido (mismo id_sonido) comparten
audio en el cache, y ese audio solo debe desaparecer cuando NINGUNO de
los dos lo sigue usando.
"""
from Core.Entities.Elementos.Abstractos.Informacion.sonido import SonidoBase, Sonido
from Services.Elemento.cache_audio import CacheAudio


def _sonido_simple(freq=440.0):
    """Dos llamadas con el mismo freq producen el mismo id_sonido (mismo
    contenido de pcm), simulando 2 Piedras con el mismo peso."""
    return SonidoBase.generar_frecuencia(0.1, freq, [1.0]).build()


class TestGuardarEnBiblioteca:
    def test_sin_cache_configurado_no_hace_nada(self):
        # Sonido debe poder usarse aislado (p.ej. en otros tests) sin
        # depender de que exista un CacheAudio -- no debe reventar.
        s = _sonido_simple()
        s.guardar_en_biblioteca()  # no lanza

    def test_con_cache_configurado_se_registra(self):
        cache = CacheAudio()
        Sonido.configurar_cache(cache)
        s = _sonido_simple()
        s.guardar_en_biblioteca()
        assert cache.tiene(s.id_sonido)

    def test_build_no_autoregistra(self):
        # Cambio de plan confirmado: build()/fusionar() NO llaman solos a
        # guardar_en_biblioteca -- es explícito, para no cachear
        # intermedios (p.ej. un operando de una fusión que no se usa
        # como sonido final).
        cache = CacheAudio()
        Sonido.configurar_cache(cache)
        s = _sonido_simple()
        assert not cache.tiene(s.id_sonido)


class TestContadorDeReferencias:
    def test_dos_sonidos_mismo_contenido_comparten_entrada_y_suman_contador(self):
        cache = CacheAudio()
        s1 = _sonido_simple(freq=440.0)
        s2 = _sonido_simple(freq=440.0)  # mismo contenido -> mismo id
        assert s1.id_sonido == s2.id_sonido

        cache.registrar(s1)
        cache.registrar(s2)

        assert len(cache._audios) == 1          # no se duplica el audio
        assert cache._contador[s1.id_sonido] == 2

    def test_liberar_una_de_dos_referencias_no_borra_el_audio(self):
        # El caso exacto reportado: Piedra A y Piedra B con mismo peso ->
        # mismo sonido. Se elimina A; B no debe quedarse sin audio.
        cache = CacheAudio()
        s1 = _sonido_simple(freq=440.0)
        s2 = _sonido_simple(freq=440.0)
        cache.registrar(s1)
        cache.registrar(s2)

        cache.liberar(s1.id_sonido)

        assert cache.tiene(s1.id_sonido)  # sigue vivo por la referencia de s2
        assert cache._contador[s1.id_sonido] == 1

    def test_liberar_la_ultima_referencia_borra_el_audio(self):
        cache = CacheAudio()
        s1 = _sonido_simple(freq=440.0)
        s2 = _sonido_simple(freq=440.0)
        cache.registrar(s1)
        cache.registrar(s2)

        cache.liberar(s1.id_sonido)
        cache.liberar(s2.id_sonido)

        assert not cache.tiene(s1.id_sonido)
        assert s1.id_sonido not in cache._contador

    def test_sonido_sin_pares_se_libera_de_una_vez(self):
        cache = CacheAudio()
        s = _sonido_simple(freq=880.0)
        cache.registrar(s)
        cache.liberar(s.id_sonido)
        assert not cache.tiene(s.id_sonido)

    def test_liberar_id_no_registrado_lanza_keyerror(self):
        import pytest
        cache = CacheAudio()
        with pytest.raises(KeyError):
            cache.liberar("id-que-no-existe")

    def test_liberar_de_biblioteca_en_sonido_delega_en_cache(self):
        cache = CacheAudio()
        Sonido.configurar_cache(cache)
        s = _sonido_simple()
        s.guardar_en_biblioteca()
        assert cache.tiene(s.id_sonido)

        s.liberar_de_biblioteca()
        assert not cache.tiene(s.id_sonido)