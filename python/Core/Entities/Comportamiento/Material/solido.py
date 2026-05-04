from Core.Entities.Comportamiento.Material.material import Material


class Solido(Material):
    def __init__(self):
        super().__init__()
        self.solido = True
