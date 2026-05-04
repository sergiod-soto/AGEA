from Core.Entities.Comportamiento.Material.material import Material


class Transparente(Material):
    def __init__(self):
        super().__init__()
        self.transparente = True
