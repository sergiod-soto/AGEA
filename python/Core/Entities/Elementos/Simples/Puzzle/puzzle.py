from abc import ABC, abstractmethod
from typing import Callable
from bitarray import bitarray


"""
    Clase padre a heredar para la generacion de puzzles.
    
    Mecanismo opaco para los bots.
    
    A cumplir:
    - coldown para cada bot
    - premio en caso de resolver
    - presentacion de estado inicial
    - acciones para interactuar
    - posible feedback de las acciones 
"""

MAX_BOTS: int = 1_000_000  # ajustar según el sistema


class Puzzle(ABC):

    class PuzzleParams:
        def __init__(
            self,
            nombre: str,
            premio,
            maquinaEstados: "Puzzle.MaquinaEstados",
            cd: int = 0,  # numero de tics que un bot tiene que esperar antes de volver a intentarlo
        ):
            self.nombre = nombre
            self.cd = cd
            self.premio = premio
            self.maquinaEstados = maquinaEstados

    class MaquinaEstados:

        class Estado:

            def __init__(
                self,
                opciones: list[Callable],
                # diferentes estados pueden tener diferentes acciones.
                # para instanciarlo, se puede hacer:
                #
                # Estado([
                #     partial(mi_funct, "Inicio"),
                #     lambda: print("Algo específico"),
                # ])
            ):
                self.opciones = opciones

            def get_opciones(self):
                return self.opciones

        def __init__(self, estados: list[Estado], estado_inicial: Estado = None):
            self.estados = estados
            self.estado_inicial = estado_inicial or estados[0]
            self.estado_actual = self.estado_inicial

        def get_estado_actual(self):
            return self.estado_actual

        def reset_maquina(self):
            self.estado_actual = self.estado_inicial

        def ejecutar_accion(self, accion: Callable) -> Estado:
            resultado = accion()
            # la acción retorna el nuevo Estado o None si no hay cambio
            self.estado_actual = resultado
            return resultado

        # _____________________________________________________________________________________________

    def __init__(self, parametros: PuzzleParams):
        self.parametros = parametros
        self._resuelto_por = bitarray(MAX_BOTS)
        self._resuelto_por.setall(0)
        self.historial: list[Callable] = []  # ↓
        # usado para guardar los pasos que ha dado el bot
        # (en ciertos puzzles, siempre estara vacio para forzar uso de la memoria)

    def get_list_acciones(self) -> list[Callable]:
        """
        retorna la lista de posibles acciones del estado actual
        """

        return self.parametros.maquinaEstados.get_estado_actual().get_opciones()

    def marcar_resuelto(self, bot_id: int) -> None:
        self._resuelto_por[bot_id] = 1

    def ha_resuelto(self, bot_id: int) -> bool:
        return self._resuelto_por[bot_id]

    def actualizar_ids(self, reasignaciones: list[tuple[int, int]]) -> None:
        for id_viejo, id_nuevo in reasignaciones:
            self._resuelto_por[id_nuevo] = self._resuelto_por[id_viejo]
            self._resuelto_por[id_viejo] = 0

    #   __________________________________________
    #   metodos a implementar por cada puzzle
    #   __________________________________________
    #
    @abstractmethod
    def reset_estado_inicial(self):
        """
        reinicia el puzzle al estado base
        """

        pass

    @abstractmethod
    def otorgar_premio(self):
        """
        retorna el premio
        """

        pass

    @abstractmethod
    def get_estado_actual(self):
        """
        retorna el estado actual del puzzle
        """

        pass

    @abstractmethod
    def check(self):
        """
        comprueba si se ha logrado el objetivo
        """

        pass
