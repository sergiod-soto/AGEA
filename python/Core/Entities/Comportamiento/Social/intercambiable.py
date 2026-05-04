from Core.Entities.Comportamiento.Social.social import Social


class Intercambiable(Social):
    def __init__(self, intercambiable: bool = True):
        super().__init__()
        self.intercambiable = intercambiable
