# Core/Entities/Elementos/Abstractos/Marcadores/Puzzle/premio.py


from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto


class Premio(Elemento_Abstracto):

    def __init__(self, **kwargs):
        super().__init__(Premio,**kwargs)
