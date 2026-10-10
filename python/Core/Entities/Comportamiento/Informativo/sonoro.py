# Core/Entities/Comportamiento/Informativo/sonoro.py

from Core.Entities.Comportamiento.Informativo.informativo import Informativo
from Core.Entities.Elementos.Abstractos.Informacion.sonido import Sonido


class Sonoro(Informativo):
    """
    Parametros:

    - sonidos: dict[str, list[Sonido]]

    Metodos abstractos:

    -
    """

    REQUIERE = {"sonidos: dict[str, list[Sonido]]"}
    ABSTRACTOS = {}

    def __init__(self, sonidos: dict[str, list[Sonido]], **kwargs):
        super().__init__(**kwargs)
        self.sonidos = sonidos

    def todos_los_sonidos(self) -> list:
        """Lista plana de todos los Sonido de todas las categorias -- para
        que quien construye el elemento (o quien gestione el mundo) pueda
        registrarlos en el CacheAudio sin que Sonoro conozca su existencia."""
        return [s for lista in self.sonidos.values() for s in lista]

    # --- Cadena serializar / representar / deserializar ---

    def serializar(self) -> dict:
        """Snapshot: audio COMPLETO de cada sonido (fidelidad total).
        (Antes se llamaba serializar_sonoros y nunca se invocaba: el hook
        de campo buscado era serializar_sonidos.)"""
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {
            "sonidos": {
                categoria: [s.serializar_audio() for s in lista]
                for categoria, lista in self.sonidos.items()
            }
        }
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Unity (cada tick): solo REFERENCIAS (id_sonido). El audio
        completo se pide aparte bajo demanda (ObtenerAudio / CacheAudio)."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {
                "sonidos": {
                    categoria: [s.id_sonido for s in lista]
                    for categoria, lista in self.sonidos.items()
                }
            }
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        self.deserializar_sonidos(data["comportamientos"][__class__.__name__]["sonidos"])

    def deserializar_sonidos(self, valor: dict) -> None:
        """
        Reconstruye Sonido reales a partir del dict de audio completo,
        para que todos_los_sonidos() siga devolviendo objetos con
        .id_sonido/.liberar_de_biblioteca()/etc. NO llama a
        guardar_en_biblioteca() aquí.
        """
        self.sonidos = {
            categoria: [Sonido.desde_audio_dict(d) for d in lista]
            for categoria, lista in valor.items()
        }

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        # Demasiado complejo para crearlo por consola.
        return []

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento emite sonidos. Demasiado complejo para crearlo por consola.

Atributos:
\tsonidos: dict[str, list[Sonido]]

Métodos:
\ttodos_los_sonidos(self) -> list
\t--------------------------------------
\tLista de todos los sonidos que puede emitir.

\tserializar(self) -> dict
\t--------------------------------------
\tSnapshot: audio completo de cada sonido.

\trepresentar(self, incluir=None) -> dict
\t--------------------------------------
\tUnity (cada tick): solo referencias (id_sonido) -- el audio
\tcompleto se pide aparte bajo demanda vía CacheAudio.

\tdeserializar_sonidos(self, valor: dict) -> None
\t--------------------------------------
\tReconstruye Sonido reales a partir del dict de audio completo.
\tNO llama a guardar_en_biblioteca() aquí.
        """