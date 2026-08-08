# Services/Elemento/cache_audio.py


class CacheAudio:
    """
    Cache de audio en memoria, direccionable por contenido (id_sonido),
    con conteo de referencias: como dos elementos con el mismo contenido
    comparten id (ver Sonido.id_sonido), el audio solo se libera cuando
    ya no queda NINGÚN elemento que lo use, no en cuanto el primero se
    elimina.
    """

    def __init__(self):
        self._audios: dict[str, dict] = {}
        self._contador: dict[str, int] = {}

    def registrar(self, sonido) -> None:
        """
        Si el id es nuevo: guarda el audio y arranca el contador en 1.
        Si ya existía (mismo contenido que otro sonido ya guardado):
        no vuelve a guardar el audio (ya está), solo incrementa el
        contador -- una referencia más apuntando al mismo audio.
        """
        id_ = sonido.id_sonido
        if id_ not in self._audios:
            self._audios[id_] = sonido.serializar_audio()
            self._contador[id_] = 1
        else:
            self._contador[id_] += 1

    def liberar(self, id_sonido: str) -> None:
        """
        Decrementa el contador de un id; cuando llega a 0 (última
        referencia eliminada), borra el audio del cache. KeyError si se
        libera un id que nunca se registró -- desequilibrio
        guardar/liberar es un error de quien llama, no un caso a
        silenciar (mismo criterio que obtener()).
        """
        self._contador[id_sonido] -= 1
        if self._contador[id_sonido] <= 0:
            del self._audios[id_sonido]
            del self._contador[id_sonido]

    def obtener(self, id_sonido: str) -> dict:
        return self._audios[id_sonido]

    def tiene(self, id_sonido: str) -> bool:
        return id_sonido in self._audios
