from Core.Entities.Comportamiento.Material.material import Material

'''
un elemento es fusionable si puede ser dividido en 2 elementos iguales de inferior cantidad
'''

class Fusionable(Material):
    def __init__(self):
        super().__init__()