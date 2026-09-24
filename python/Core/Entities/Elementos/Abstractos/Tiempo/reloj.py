# Core/Entities/Elementos/Abstractos/Tiempo/reloj.py

from typing import Tuple

from numpy import uint64

from Config.parametros_simulacion import TICKS_POR_SEGUNDO
from Config.settings import ID_RELOJ
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.marcador_temporal import (
    Marcador_Temporal,
)
from Core.Entities.Elementos.elemento import Elemento


class Reloj(Marcador_Temporal):

    segundos: uint64 = 0

    def Segundo(self, cantidad) -> int:
        return TICKS_POR_SEGUNDO * cantidad

    def Minuto(self, cantidad) -> int:
        return self.Segundo(cantidad) * 60

    def Hora(self, cantidad) -> int:
        return self.Minuto(cantidad) * 60

    def Dia(self, cantidad) -> int:
        return self.Hora(cantidad) * 24

    def Mes(self, cantidad) -> int:
        return self.Dia(cantidad) * 30

    def Anho(self, cantidad) -> int:
        return self.Mes(cantidad) * 12

    class Ciclo:

        def __init__(
            self,
            elemento: Elemento,
            end: int,
            start: int = 0,
            paso: int = 1,
        ):
            self.elemento = elemento
            self._end = end
            self._paso = paso
            self.tick_actual = start
            self._contador = 0

        def next_tick(self) -> None:
            self._contador += 1

            if self._contador < self._paso:
                return

            self._contador = 0
            self.tick_actual += 1

            if self.tick_actual >= self._end:
                self.tick_actual = 0

    ciclos: list["Reloj.Ciclo"] = []

    def __init__(self, **kwargs):
        super().__init__(Reloj, id_elemento=ID_RELOJ, **kwargs)

    def avanzar_un_segundo(self) -> None:
        self.segundos += 1

    def avanzar_un_minuto(self) -> None:
        self.segundos += 60

    def avanzar_una_hora(self) -> None:
        self.segundos += 3600

    def avanzar_segundos(self, segundos: int) -> None:
        self.segundos += segundos

    def get_tiempo(self) -> uint64:
        return self.segundos

    def get_tiempo_formateado(self) -> Tuple[int, int, int]:
        minutos = self.segundos // 60
        segundos = self.segundos % 60

        horas = minutos // 60
        minutos = minutos % 60

        return [horas, minutos, segundos]

    def set_tiempo(self, segundos: int) -> None:
        self.segundos = segundos

    def set_tiempo_formateado(self, hora: tuple[int, int, int]) -> None:
        self.segundos: uint64 = hora[0] * 3600 + hora[1] * 60 + hora[2]

    def agregar_ciclo(
        self, elemento: Elemento, end: int, start: int = 0, paso: int = 1
    ) -> Ciclo:
        ciclo = self.Ciclo(elemento, end, start, paso)
        Reloj.ciclos.append(ciclo)
        return ciclo

    def eliminar_ciclo(self, ciclo: Ciclo) -> None:
        Reloj.ciclos.remove(ciclo)

    def next_tick(self) -> None:
        self.avanzar_un_segundo()
        for ciclo in Reloj.ciclos:
            ciclo.next_tick()
