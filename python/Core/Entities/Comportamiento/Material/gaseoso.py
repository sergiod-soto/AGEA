from Core.Entities.Comportamiento.Material.material import Material


class Gaseoso(Material):
    def __init__(self):
        super().__init__()
        self.gaseoso = True
