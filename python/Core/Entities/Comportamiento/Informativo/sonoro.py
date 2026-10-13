# Core/Entities/Comportamiento/Informativo/sonoro.py

from Core.Entities.Comportamiento.Informativo.informativo import Informativo
from Core.Entities.Elementos.Abstractos.Informacion.sonido import Sonido


class Sonoro(Informativo):
    """
    El Elemento emite sonidos, agrupados por categoría.

    Parametros:

    - sonidos: dict[str, list[Sonido]]

    Serialización (dos niveles):
    - serializar()  -> snapshots: cada Sonido con TODA su información
                       (Sonido.serializar(): id, duracion, vol, vector, pcm).
    - representar() -> por defecto: cada Sonido se representa con
                       Sonido.representar() (en esencia, su id). El pcm se
                       pide aparte bajo demanda (ObtenerAudio).
    """

    REQUIERE = {"sonidos: dict[str, list[Sonido]]"}
    ABSTRACTOS = {}

    def __init__(self, sonidos: dict[str, list[Sonido]], **kwargs):
        super().__init__(**kwargs)
        self.sonidos = sonidos

    def todos_los_sonidos(self) -> list:
        """Lista plana de todos los Sonido de todas las categorías, para
        que quien construye el elemento (o gestiona el mundo) pueda
        registrarlos en el CacheAudio sin que Sonoro conozca su existencia."""
        return [s for lista in self.sonidos.values() for s in lista]

    # --- Hooks por campo ---

    def serializar_sonidos(self) -> dict:
        """Cada Sonido con toda su información (Sonido.serializar()).
        También lo usa aplicar_patch (clave "sonidos"), simétrico a
        deserializar_sonidos."""
        return {
            categoria: [s.serializar() for s in lista]
            for categoria, lista in self.sonidos.items()
        }

    def deserializar_sonidos(self, valor: dict) -> None:
        """
        Reconstruye Sonido reales desde el dict de audio completo, para que
        todos_los_sonidos() devuelva objetos con .id_sonido,
        .liberar_de_biblioteca(), etc. NO llama a guardar_en_biblioteca().
        """
        self.sonidos = {
            categoria: [Sonido.desde_audio_dict(d) for d in lista]
            for categoria, lista in valor.items()
        }

    # --- Cadena serializar / representar / deserializar ---

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {
            "sonidos": self.serializar_sonidos()
        }
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Cada Sonido se representa con su propio representar(): sin
        vector ni pcm. Se le pasa None (sin filtro) a propósito: `incluir`
        ya se aplicó arriba a Sonoro; si se reenviara, un filtro con
        "Sonoro" dejaría a cada Sonido con su parte vacía."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {
                "sonidos": {
                    categoria: [s.representar(None) for s in lista]
                    for categoria, lista in self.sonidos.items()
                }
            }
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        self.deserializar_sonidos(
            data["comportamientos"][__class__.__name__]["sonidos"]
        )

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
\tSnapshots: cada Sonido con toda su información
\t(id, duracion, vol, vector, pcm).

\trepresentar(self, incluir=None) -> dict
\t--------------------------------------
\tCada Sonido se representa con Sonido.representar() (en esencia, su id).

\tdeserializar_sonidos(self, valor: dict) -> None
\t--------------------------------------
\tReconstruye Sonido reales a partir del dict de audio completo.
\tNO llama a guardar_en_biblioteca() aquí.
        """
