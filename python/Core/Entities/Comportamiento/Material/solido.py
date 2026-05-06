from Core.Entities.Comportamiento.Material.material import Material


class Solido(Material):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.solido = True
