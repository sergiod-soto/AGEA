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
            
        ):
            self.nombre = nombre
            self.cd = cd
            self.premio = premio
            self.acciones = acciones
            
    class MaquinaEstados:

        class Estado:            
            def __init__():
                pass
            
        def __init__():
            pass

    def __init__(self, parametros: PuzzleParams):
        self.parametros = parametros

    @abstractmethod
    def reset_estado_inicial(self):
        pass
    
    def get_list_acciones(self) -> list[function]:
        return self.parametros.acciones
    
    @abstractmethod
    def get_premio(self):
        pass
    
    @abstractmethod
    def get_estado_actual(self):
        pass
    
