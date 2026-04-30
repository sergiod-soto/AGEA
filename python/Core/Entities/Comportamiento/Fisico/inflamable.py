from Core.Entities.Comportamiento.Fisico.fisico import Fisico

import time


class Inflamable(Fisico):

    def __init__(self, temperatura_ignicion: float):
        super().__init__()
        self.temperatura_ignicion = temperatura_ignicion
        self.inflamable = True
        self.ardiendo = False
        self.tiempo_total_quemado = 0.0
        self.tiempo_encendido = 0.0

    def encender(self):

        if not self.inflamable:
            return

        if self.ardiendo:
            return

        self.ardiendo = True
        self.tiempo_encendido = time()

    def apagar(self):

        self.ardiendo = False
        self.tiempo_total_quemado += time() - self.tiempo_encendido
