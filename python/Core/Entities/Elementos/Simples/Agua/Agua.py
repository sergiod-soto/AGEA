from Core.Entities.Comportamiento.Fisico.peso import Peso
from Core.Entities.Comportamiento.Material.liquido import Liquido
from Core.Entities.Elementos.Simples.elemento_simple import Elemento_Simple
from Core.Entities.Comportamiento.comportamiento import Comportamiento as C


comportamientos = C.declarar_comportamientos(

)


class Agua(Elemento_Simple, comportamientos):

    def __init__(self):
        super().__init__()
