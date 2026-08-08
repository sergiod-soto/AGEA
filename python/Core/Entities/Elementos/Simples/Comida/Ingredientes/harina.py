from Core.Entities.Comportamiento.comportamiento import Comportamiento


comportamientos = Comportamiento.declarar_comportamientos(

)


# TODO: definir harina
class Harina(comportamientos):
    def __init__(self, tipo, casilla, capa):
        super().__init__(Harina, casilla, capa)
