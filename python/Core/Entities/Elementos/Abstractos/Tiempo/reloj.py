# Core/Entities/Elementos/Abstractos/Tiempo/reloj.py

from typing import Callable, Tuple

from Config.parametros_simulacion import SEGUNDOS_SIMULADOS_TICK
from Config.settings import ID_RELOJ
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.marcador_temporal import (
    Marcador_Temporal,
)
from Core.Entities.Elementos.elemento import Elemento


class Reloj(Marcador_Temporal):
    """
    Reloj del mundo. Cuenta tiempo SIMULADO: cada tick avanza el reloj
    SEGUNDOS_SIMULADOS_TICK segundos y hace avanzar un paso a cada Ciclo
    (solar, lunar, estación...), que se miden en TICKS.
    """

    # ------------------------------------------------------------------
    #  Conversión de tiempo simulado a TICKS
    #
    #  Segundo/Minuto/.../Anho devuelven cuántos TICKS dura esa cantidad de
    #  tiempo simulado (se usan, p. ej., para fijar la duración de un Ciclo).
    #  ticks = segundos / SEGUNDOS_SIMULADOS_TICK: si cada tick avanza 2 s,
    #  10 s son 5 ticks. (Antes MULTIPLICABA por SEGUNDOS_SIMULADOS_TICK, lo
    #  que era correcto con el antiguo TICKS_POR_SEGUNDO pero quedó invertido
    #  al renombrar; con el valor 1.0 no se notaba.)
    #
    #  Todo parte de Segundo() y se redondea UNA sola vez, para no acumular
    #  error de redondeo al encadenar minuto -> hora -> día...
    #  Convención: 1 mes = 30 días, 1 año = 12 meses (360 días).
    # ------------------------------------------------------------------

    def Segundo(self, cantidad) -> int:
        return round(cantidad / SEGUNDOS_SIMULADOS_TICK)

    def Minuto(self, cantidad) -> int:
        return self.Segundo(cantidad * 60)

    def Hora(self, cantidad) -> int:
        return self.Segundo(cantidad * 60 * 60)

    def Dia(self, cantidad) -> int:
        return self.Segundo(cantidad * 60 * 60 * 24)

    def Mes(self, cantidad) -> int:
        return self.Dia(cantidad * 30)

    def Anho(self, cantidad) -> int:
        return self.Mes(cantidad * 12)

    class Ciclo:

        def __init__(
            self,
            elemento: Elemento,
            end: int,
            start: int = 0,
            paso: int = 1,  # cada cuantos ticks 'tick_actual' debe avanzar 1
            al_avanzar: Callable[[int], None] | None = None,
        ):

            if end <= 0:
                raise ValueError(f"Ciclo: 'end' debe ser > 0 (recibido {end}).")
            if paso < 1:
                raise ValueError(f"Ciclo: 'paso' debe ser >= 1 (recibido {paso}).")

            self.elemento = elemento
            self._end = end
            self._paso = paso
            self.tick_actual = start
            self._contador_paso = 0
            self._al_avanzar = al_avanzar

        def next_tick(self) -> None:
            # _contador_paso
            self._contador_paso += 1
            if self._contador_paso < self._paso:
                return
            self._contador_paso = 0

            # tick_actual
            self.tick_actual += 1
            if self.tick_actual < self._end:
                return
            self.tick_actual = 0

            if self._al_avanzar is not None:
                self._al_avanzar(self.tick_actual)

        @property
        def progreso(self) -> float:
            """Fracción del ciclo recorrida, en [0, 1)."""
            return self.tick_actual / self._end

        @property
        def duracion(self) -> int:
            """Duración total del ciclo, en ticks."""
            return self._end

    def __init__(self, **kwargs):
        super().__init__(Reloj, id_elemento=ID_RELOJ, **kwargs)

        # Segundos SIMULADOS transcurridos. float porque un tick puede
        # avanzar una fracción de segundo (SEGUNDOS_SIMULADOS_TICK < 1).
        self.segundos: float = 0.0

        # Ciclos registrados, POR INSTANCIA. Antes era un atributo de CLASE
        # (compartido por todos los Reloj): con dos instancias (tests, un
        # Mundo recreado) los ciclos se acumulaban y avanzaban dos veces por
        # tick.
        self.ciclos: list["Reloj.Ciclo"] = []

    def avanzar_un_segundo(self) -> None:
        self.segundos += 1

    def avanzar_un_minuto(self) -> None:
        self.segundos += 60

    def avanzar_una_hora(self) -> None:
        self.segundos += 3600

    def avanzar_segundos(self, segundos: float) -> None:
        self.segundos += segundos

    def get_tiempo(self) -> float:
        return self.segundos

    def get_tiempo_formateado(self) -> Tuple[int, int, int]:
        """(horas, minutos, segundos) del tiempo simulado, enteros."""
        total = int(self.segundos)
        minutos = total // 60
        segundos = total % 60

        horas = minutos // 60
        minutos = minutos % 60

        return (horas, minutos, segundos)

    def set_tiempo(self, segundos: float) -> None:
        self.segundos = segundos

    def set_tiempo_formateado(self, hora: tuple[int, int, int]) -> None:
        self.segundos = hora[0] * 3600 + hora[1] * 60 + hora[2]

    def agregar_ciclo(
        self,
        elemento: Elemento,
        end: int,
        start: int = 0,
        paso: int = 1,
        al_avanzar: Callable[[int], None] | None = None,
    ) -> Ciclo:
        ciclo = self.Ciclo(elemento, end, start, paso, al_avanzar)
        self.ciclos.append(ciclo)
        return ciclo

    def eliminar_ciclo(self, ciclo: Ciclo) -> None:
        self.ciclos.remove(ciclo)

    def next_tick(self) -> None:
        """Avanza un tick: el reloj suma SEGUNDOS_SIMULADOS_TICK segundos
        (antes sumaba siempre 1) y cada ciclo avanza un paso."""
        self.avanzar_segundos(SEGUNDOS_SIMULADOS_TICK)
        for ciclo in self.ciclos:
            ciclo.next_tick()

    def volcar_estado(self) -> dict:
        """
        Estado mínimo para un snapshot: segundos simulados y, por cada ciclo en
        el ORDEN de registro (solar, lunar, estación: el de Mundo.__init__),
        su tick actual y el contador de paso.
        """
        return {
            "segundos": self.segundos,
            "ciclos": [
                {"tick_actual": c.tick_actual, "contador": c._contador_paso}
                for c in self.ciclos
            ],
        }

    def restaurar_estado(self, estado: dict) -> None:
        """
        Inverso de volcar_estado(). Se valida TODO antes de tocar nada, y los
        ciclos se actualizan EN SITIO (no se recrean).
        ValueError si el snapshot no encaja con los ciclos actuales.
        """
        guardados = estado["ciclos"]
        if len(guardados) != len(self.ciclos):
            raise ValueError(
                f"Reloj: el snapshot tiene {len(guardados)} ciclos y el mundo "
                f"{len(self.ciclos)}."
            )
        for ciclo, g in zip(self.ciclos, guardados):
            if not 0 <= g["tick_actual"] < ciclo._end:
                raise ValueError(
                    f"Reloj: tick_actual {g['tick_actual']} fuera de [0, {ciclo._end})."
                )
        self.segundos = estado["segundos"]
        for ciclo, g in zip(self.ciclos, guardados):
            ciclo.tick_actual = g["tick_actual"]
            ciclo._contador_paso = g["contador"]
