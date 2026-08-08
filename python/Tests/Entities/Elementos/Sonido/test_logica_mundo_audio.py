# Tests/Entities/Elementos/Sonido/test_logica_mundo_audio.py
"""
Tests de LogicaMundo.obtener_audio() y de la liberación de sonidos al
eliminar un elemento. Se usa un elemento de prueba mínimo (solo con
todos_los_sonidos()) en vez de una Piedra real, porque _liberar_sonidos_de
solo depende de esa interfaz (ver logica_mundo.py) -- no hace falta el
mixin completo de Sonoro para probar esta parte.
"""

import pytest

from Infraestructura.Gestores.Mundo.Logica_Mundo.logica_mundo import LogicaMundo, Celda
from Core.Entities.Elementos.Abstractos.Informacion.sonido import SonidoBase


class _ElementoConSonidos:
    """Doble de test: cualquier objeto con todos_los_sonidos() basta para
    _liberar_sonidos_de -- no se necesita el mixin Sonoro real aquí."""

    def __init__(self, sonidos: list):
        self._sonidos = sonidos

    def todos_los_sonidos(self) -> list:
        return self._sonidos


def _sonido_simple(freq=440.0):
    return SonidoBase.generar_frecuencia(0.1, freq, [1.0]).build()


@pytest.fixture
def logica():
    # gestor_bots_client=None es válido (ver matar_bot, que ya contempla
    # este caso) -- no hace falta un cliente real para estos tests.
    return LogicaMundo(gestor_bots_client=None)


class TestObtenerAudio:
    @pytest.mark.asyncio
    async def test_id_registrado_devuelve_payload(self, logica):
        s = _sonido_simple()
        s.guardar_en_biblioteca()  # LogicaMundo.__init__ ya configuró el cache

        ok, error, audio_bytes = await logica.obtener_audio(s.id_sonido)

        assert ok is True
        assert error == ""
        import json

        payload = json.loads(audio_bytes.decode())
        assert payload["id"] == s.id_sonido
        assert "vector" in payload and "pcm" in payload

    @pytest.mark.asyncio
    async def test_id_no_registrado_devuelve_error(self, logica):
        ok, error, audio_bytes = await logica.obtener_audio("id-inexistente")
        assert ok is False
        assert error != ""
        assert audio_bytes == b""


class TestLiberacionAlEliminar:
    @pytest.mark.asyncio
    async def test_eliminar_elemento_libera_sus_sonidos(self, logica):
        s = _sonido_simple()
        s.guardar_en_biblioteca()
        elemento = _ElementoConSonidos([s])

        eid = 1
        logica._elements[eid] = elemento
        logica._gold_cells[(0, 0)] = Celda(resto=[eid])

        ok, error = await logica.eliminar_elemento((0, 0), eid)

        assert ok is True
        assert not logica._cache_audio.tiene(s.id_sonido)

    @pytest.mark.asyncio
    async def test_eliminar_una_de_dos_piedras_con_mismo_sonido_no_borra_audio(
        self, logica
    ):
        # El caso original reportado por el usuario, de punta a punta:
        # 2 elementos con el mismo sonido -> eliminar uno no debe dejar
        # al otro huérfano de audio.
        s1 = _sonido_simple(freq=440.0)
        s2 = _sonido_simple(freq=440.0)
        assert s1.id_sonido == s2.id_sonido
        s1.guardar_en_biblioteca()
        s2.guardar_en_biblioteca()

        elemento_a = _ElementoConSonidos([s1])
        elemento_b = _ElementoConSonidos([s2])
        logica._elements[1] = elemento_a
        logica._elements[2] = elemento_b
        logica._gold_cells[(0, 0)] = Celda(resto=[1])
        logica._gold_cells[(1, 1)] = Celda(resto=[2])

        ok, error = await logica.eliminar_elemento((0, 0), 1)

        assert ok is True
        assert logica._cache_audio.tiene(s1.id_sonido)  # sigue vivo por elemento_b

    @pytest.mark.asyncio
    async def test_elemento_sin_sonidos_no_falla_al_eliminar(self, logica):
        # hasattr(elemento, "todos_los_sonidos") debe filtrar
        # correctamente elementos que no son Sonoro -- no debe intentar
        # liberar nada ni reventar.
        class _ElementoSinSonidos:
            pass

        eid = 5
        logica._elements[eid] = _ElementoSinSonidos()
        logica._gold_cells[(2, 2)] = Celda(resto=[eid])

        ok, error = await logica.eliminar_elemento((2, 2), eid)
        assert ok is True

    @pytest.mark.asyncio
    async def test_aplicar_crear_sin_lock_registra_sonidos(self, logica):
        """
        Simula un Sector creando un elemento (aplicar_delta_sector ->
        _aplicar_crear_sin_lock): el sonido de la Piedra se generó en
        OTRO proceso (donde Sonido._cache_audio nunca estuvo configurado,
        ver conversación), así que el registro real tiene que pasar aquí,
        no en Piedra.__init__.
        """
        elemento = _ElementoConSonidos([_sonido_simple()])

        # Doble de test para CrearElemento: no se asume la clase real de
        # mutaciones.py, solo los atributos que _aplicar_crear_sin_lock lee.
        class _CrearElementoFake:
            def __init__(self, elemento, pos, tipo_slot):
                self.elemento = elemento
                self.pos = pos
                self.tipo_slot = tipo_slot
                self.marcador_local = "test"

        m = _CrearElementoFake(elemento, (3, 3), "resto")

        async with logica._lock:
            logica._aplicar_crear_sin_lock(m)

        s = elemento.todos_los_sonidos()[0]
        assert logica._cache_audio.tiene(s.id_sonido)

    @pytest.mark.asyncio
    async def test_crear_elemento_rpc_registra_sonidos(self, logica, monkeypatch):
        """
        Mismo caso vía el RPC CrearElemento: el elemento llega ya
        serializado en bytes. Se monkeypatchea _slot_bytes_a_id (en vez
        de construir un JSON real con reconstruir_elemento, cuyo formato
        exacto no está confirmado) para aislar lo que sí es nuevo aquí:
        que crear_elemento llama a _registrar_sonidos_de tras resolver
        el elemento.
        """
        elemento = _ElementoConSonidos([_sonido_simple()])
        eid = 42

        def _fake_slot_bytes_a_id(blob):
            logica._elements[eid] = elemento
            return eid

        monkeypatch.setattr(logica, "_slot_bytes_a_id", _fake_slot_bytes_a_id)

        ok, error = await logica.crear_elemento((0, 0), "resto", b"cualquier-cosa")

        assert ok is True
        s = elemento.todos_los_sonidos()[0]
        assert logica._cache_audio.tiene(s.id_sonido)

    @pytest.mark.asyncio
    async def test_elemento_sin_sonidos_no_falla_al_crear(self, logica):
        # Mismo filtro hasattr que ya se probó al eliminar -- aquí se
        # confirma que tampoco falla en el lado de creación.
        class _ElementoSinSonidos:
            pass

        class _CrearElementoFake:
            def __init__(self, elemento, pos, tipo_slot):
                self.elemento = elemento
                self.pos = pos
                self.tipo_slot = tipo_slot
                self.marcador_local = "test"

        m = _CrearElementoFake(_ElementoSinSonidos(), (4, 4), "resto")

        async with logica._lock:
            logica._aplicar_crear_sin_lock(m)  # no debe lanzar
