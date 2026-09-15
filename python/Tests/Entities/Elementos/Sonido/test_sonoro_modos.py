# Tests/Entities/Elementos/Sonido/test_sonoro_modos.py
"""
Tests del mecanismo de 3 modos en Comportamiento.serializar() aplicado a
Sonoro: "guardado"/"transporte" deben llevar audio completo (fidelidad
para reconstruir el elemento); "representacion" debe llevar solo
referencias (lo que ve Unity cada tick).
"""

import pytest
from Core.Entities.Comportamiento.Informativo.sonoro import Sonoro
from Core.Entities.Elementos.Abstractos.Informacion.sonido import Sonido, SonidoBase
from Core.Entities.entity import Modos
from Services.Elemento.cache_audio import CacheAudio


def _sonido_simple(freq=440.0):
    return SonidoBase.generar_frecuencia(0.1, freq, [1.0]).build()


def _sonoro_de_ejemplo():
    return Sonoro(
        sonidos={
            "GOLPEAR": [_sonido_simple(440.0)],
            "EMPUJAR": [_sonido_simple(220.0), _sonido_simple(110.0)],
        }
    )


class TestModoRepresentacion:
    def test_solo_referencias_sin_vector_ni_pcm(self):
        s = _sonoro_de_ejemplo()
        data = s.serializar(modo=Modos.transporte)
        for lista in data["sonidos"].values():
            for entrada in lista:
                assert set(entrada.keys()) == {"id", "duracion", "vol"}

    def test_es_json_serializable(self):
        import json

        s = _sonoro_de_ejemplo()
        json.dumps(s.serializar(modo=Modos.transporte))  # no debe lanzar


class TestModosCompletoFidelidad:
    @pytest.mark.parametrize("modo", ["guardado", "transporte"])
    def test_incluye_vector_y_pcm(self, modo):
        s = _sonoro_de_ejemplo()
        data = s.serializar(modo=modo)
        for lista in data["sonidos"].values():
            for entrada in lista:
                assert "vector" in entrada
                assert "pcm" in entrada

    @pytest.mark.parametrize("modo", ["guardado", "transporte"])
    def test_es_json_serializable(self, modo):
        import json

        s = _sonoro_de_ejemplo()
        json.dumps(s.serializar(modo=modo))  # este es el bug original: reventaba aquí

    def test_guardado_y_transporte_dan_el_mismo_resultado_hoy(self):
        # Documenta la decisión explícita: hoy son idénticos porque caen
        # los dos al mismo hook genérico serialize_sonidos(). Si algún
        # día divergen, este test debe romperse a propósito -- señal de
        # que hay que revisar si el cambio fue intencional.
        s = _sonoro_de_ejemplo()
        assert s.serializar(modo=Modos.guardado) == s.serializar(modo=Modos.transporte)


class TestModoEsObligatorio:
    def test_serializar_sin_modo_lanza_typeerror(self):
        # Decisión explícita: sin valor por defecto, para forzar a
        # cualquier consumidor nuevo a elegir modo conscientemente.
        s = _sonoro_de_ejemplo()
        with pytest.raises(TypeError):
            s.serializar()


class TestDeserializarSonidos:

    def test_reconstruye_objetos_sonido_reales(self):
        original = _sonoro_de_ejemplo()
        data = original.serializar(modo=Modos.transporte)

        reconstruido = Sonoro(sonidos={})
        reconstruido.deserialize_sonidos(data["sonidos"])

        for lista in reconstruido.sonidos.values():
            for s in lista:
                assert isinstance(s, Sonido)

    def test_conserva_los_mismos_ids(self):
        original = _sonoro_de_ejemplo()
        data = original.serializar(modo=Modos.transporte)
        reconstruido = Sonoro(sonidos={})
        reconstruido.deserialize_sonidos(data["sonidos"])

        ids_originales = {s.id_sonido for l in original.sonidos.values() for s in l}
        ids_reconstruidos = {
            s.id_sonido for l in reconstruido.sonidos.values() for s in l
        }
        assert ids_originales == ids_reconstruidos

    def test_todos_los_sonidos_utilizable_tras_reconstruir(self):
        # El caso concreto que motivó esto: tras reconstruir, los objetos
        # deben poder liberarse igual que uno recién creado (necesario
        # para _liberar_sonidos_de en LogicaMundo).
        original = _sonoro_de_ejemplo()
        data = original.serializar(modo=Modos.transporte)
        reconstruido = Sonoro(sonidos={})
        reconstruido.deserialize_sonidos(data["sonidos"])

        cache = CacheAudio()
        Sonido.configurar_cache(cache)
        for s in reconstruido.todos_los_sonidos():
            s.guardar_en_biblioteca()
            s.liberar_de_biblioteca()  # no debe lanzar

    def test_deserializar_no_toca_el_cacheaudio(self):
        """
        Punto crítico: deserialize_sonidos NO debe autoregistrar en el
        cache. Si lo hiciera, cada resincronización de celdas
        (actualizar_celdas, llamado en cada ciclo de tick) incrementaría
        el contador de referencias sin una liberación correspondiente, y
        el audio jamás llegaría a 0.
        """
        cache = CacheAudio()
        Sonido.configurar_cache(cache)

        original = _sonoro_de_ejemplo()
        data = original.serializar(modo=Modos.transporte)

        reconstruido = Sonoro(sonidos={})
        reconstruido.deserialize_sonidos(data["sonidos"])

        assert len(cache._audios) == 0
