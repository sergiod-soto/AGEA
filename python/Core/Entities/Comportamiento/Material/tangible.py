from Core.Entities.Comportamiento.Material.material import Material


class Tangible(Material):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.tangible = True
