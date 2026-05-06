from Core.Entities.Comportamiento.Social.social import Social


class Intercambiable(Social):

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.intercambiable: bool = True
