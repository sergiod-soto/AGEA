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

    def serialize_sonidos(self) -> dict:
        """Hook genérico: fidelidad completa. Cubre 'guardado' y 'transporte'
        por fallback (ver Comportamiento.serializar) mientras ambos necesiten
        lo mismo. El día que uno de los dos necesite algo distinto, se le
        añade su propio serialize_sonidos_guardado() o
        serialize_sonidos_transporte() sin tocar este ni la firma de nada."""
        return {
            categoria: [s.serializar_audio() for s in lista]
            for categoria, lista in self.sonidos.items()
        }

    def serialize_sonidos_representacion(self) -> dict:
        """Modo 'representacion' (Unity, cada tick): solo referencias -- el
        audio completo se pide aparte bajo demanda vía CacheAudio."""
        return {
            categoria: [s.serializar_referencia() for s in lista]
            for categoria, lista in self.sonidos.items()
        }

    def deserialize_sonidos(self, valor: dict) -> None:
        """
        Contraparte de serialize_sonidos(): reconstruye Sonido reales a
        partir del dict de audio completo, para que todos_los_sonidos() siga
        devolviendo objetos con .id_sonido/.liberar_de_biblioteca()/etc. tras
        reconstruir un elemento (ver piedra.py, bug detectado). NO llama a
        guardar_en_biblioteca() aquí.
        """
        self.sonidos = {
            categoria: [Sonido.desde_audio_dict(d) for d in lista]
            for categoria, lista in valor.items()
        }

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "peso",
        ]

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

\tserialize_sonidos(self) -> dict
\t--------------------------------------
\tRecarga energía.

\tserialize_sonidos_representacion(self) -> dict
\t--------------------------------------
\tModo 'representacion' (Unity, cada tick): solo referencias -- el
\taudio completo se pide aparte bajo demanda vía CacheAudio.

\tdeserialize_sonidos(self, valor: dict) -> None
\t--------------------------------------
\tContraparte de serialize_sonidos(): reconstruye Sonido reales a
\tpartir del dict de audio completo, para que todos_los_sonidos() siga
\tdevolviendo objetos con .id_sonido/.liberar_de_biblioteca()/etc. tras
\treconstruir un elemento (ver piedra.py, bug detectado). NO llama a 
\tguardar_en_biblioteca() aquí.
        """

    def representar_sonoro(self) -> list[str]:
        """
        Informacion pasada a Unity para representar el Elemento
        """

        representacion = {
            "sonoro": self.serialize_sonidos_representacion(),
        }
        return representacion
