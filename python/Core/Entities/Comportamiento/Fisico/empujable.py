from abc import abstractmethod

from Core.Entities.Comportamiento.Fisico.fisico import Fisico
from Core.Entities.Elementos.elemento import Elemento


class Empujable(Fisico):

    def __init__(self, coste_empujar: float):
        super().__init__()

        self.coste_empujar = coste_empujar  #   cuanta energia drena moverlo 1 ud.
        self.empujable: bool = True

    def calcular_coste_empujar_en_cadena(self, direccion) -> float:
        """
        Compruebo el coste de mover algo. si no puede moverse, o choca contra
        algo que no puede ser movido, retorna -1.
        Si puede moverse y no choca, retorna el coste propio.
        Si puede moverse pero choca, retorna el coste sumado
        """

        check = self.check_push(direccion)
        if check is True:
            return self.coste_empujar
        if check is False:
            return -1.0
        if isinstance(check, Elemento):
            # choca, asi que en check debe haber un Elemento
            #
            # compruebo si tiene el comportamiento 'Empujable'
            if check.tiene_comportamiento(Empujable):
                return self.coste_empujar + check.calcular_coste_empujar_en_cadena(
                    direccion
                )
            else:
                return False

    @abstractmethod
    def check_push(self, direccion) -> Elemento | True | False:
        """
        Intenta mover la entidad una celda en `direccion`.
        Devuelve un Elemento si choca contra algo, True si tendria exito o False si no puede.
        """
        pass

    @abstractmethod
    def push(self, direccion) -> bool:
        pass
