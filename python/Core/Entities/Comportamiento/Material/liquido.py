from Core.Entities.Comportamiento.Material.material import Material


class Liquido(Material):
    def __init__(self):
        super().__init__()
        self.liquido = True
