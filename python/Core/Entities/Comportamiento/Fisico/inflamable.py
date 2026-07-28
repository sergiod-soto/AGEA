from Core.Entities.Comportamiento.Fisico.fisico import Fisico

import time


class Inflamable(Fisico):
    """
    Parametros:

    - temperatura_ignicion: float

    Metodos abstractos:

    -
    """

    def __init__(self, temperatura_ignicion: float, **kwargs):
        super().__init__(**kwargs)
        self.temperatura_ignicion = (
            temperatura_ignicion  #   temperatura para comenzar a arder
        )
        self.ardiendo: bool = False
        self._tiempo_total_quemado = 0.0
        self._hora_encendido = None

    @classmethod
    def _campos_internos(cls):
        return {
            "ardiendo",
            "_tiempo_total_quemado",
            "_hora_encendido",
        }

    def encender(self):
        if not self.inflamable:
            return

        if self.ardiendo:
            return

        self.ardiendo = True
        self._hora_encendido = time()

    def apagar(self):
        self.ardiendo = False
        self._tiempo_total_quemado += time() - self._hora_encendido
        self

    def get_tiempo_total_quemado(self) -> float:
        if self.ardiendo is False:
            return self._tiempo_total_quemado
        else:
            return self._tiempo_total_quemado + (time() - self._hora_encendido)
