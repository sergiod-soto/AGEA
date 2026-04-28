from abc import ABC, abstractmethod

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


class Puzzle(ABC):

    class PuzzleParams:
        def __init__(
            self,
            nombre: str,
            cd: int,
            premio,
            acciones: list[function],
            maquinaEstados: Puzzle.MaquinaEstados,
        ):
            self.nombre = nombre
            self.cd = cd
            self.premio = premio
            self.acciones = acciones
            self.maquinaEstados = maquinaEstados

    class MaquinaEstados:

        class Estado:

            def __init__(
                self,
                opciones: list[function],
                # puede que, segun el estado, se puedan realizar diferentes acciones.
                # para instanciarlo, se puede hacer:
                # ([
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
            self.estado_actual = estado_inicial

        def get_estado_actual(self):
            return self.estado_actual

        def reset_maquina(self):
            self.estado_actual = self.estados[0]

    # _____________________________________________________________________________________________

    def __init__(self, parametros: PuzzleParams):
        self.parametros = parametros

    def get_list_acciones(self) -> list[function]:
        """
        retorna la lista de posibles acciones del estado actual
        """

        return self.parametros.acciones

    def reset_estado_inicial(self):
        """
        reinicia el puzzle al estado base
        """

        pass

    @abstractmethod
    def get_premio(self):
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
