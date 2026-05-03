from Core.Entities.Comportamiento.Material.material import Material

class Transformable(Material):
    '''Elemento que, al darse determinadas circunstancias, es cambiado por otro (madera + calor -> ceniza)'''
    def __init__(self):
        super().__init__()