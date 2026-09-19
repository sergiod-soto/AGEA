class Bioma:

    def __init__(
        self,
        tipo,
        tasa_conversion_radiacion_calor,
        inercia_termica,
        **kwargs,
    ):
        super().__init__(
            tipo,
            **kwargs,
        )

        self.inercia_termica = inercia_termica
        self.tasa_conversion_radiacion_calor = tasa_conversion_radiacion_calor
