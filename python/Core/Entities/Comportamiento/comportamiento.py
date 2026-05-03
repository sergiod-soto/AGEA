class Comportamiento:

    def __init__(self):
        super().__init__()

    def comportamientos(self) -> list["Comportamiento"]:
        """Retorna todos los comportamientos de la entidad"""

        return [
            c
            for c in type(self).__mro__
            if issubclass(c, Comportamiento) and c is not Comportamiento
        ]

    def comportamientos_de(self, categoria) -> list["Comportamiento"]:
        """Retorna que comportamientos se han heredado de cierta categoria"""

        return [
            c
            for c in type(self).__mro__
            if issubclass(c, categoria) and c is not categoria
        ]

    def categorias(self) -> list["Comportamiento"]:
        """
        retorna las categorias con comportamientos presentes en la entidad
        """

        categorias = Comportamiento.__subclasses__()
        return [c for c in type(self).__mro__ if c in categorias]

    def tiene_comportamiento(self, comportamiento) -> bool:
        """Pregunta si el elemento tiene X comportamiento"""
        return isinstance(self, comportamiento)

    # --- Representación ---
    def __repr__(self):
        nombres = [c.__name__ for c in self.comportamientos()]
        return f"{type(self).__name__}({', '.join(nombres)})"

    # --- Serialización  ---
    def a_dict(self) -> dict:
        """Exporta el estado del objeto como diccionario"""
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def desde_dict(cls, datos: dict):
        obj = cls.__new__(cls)
        obj.__dict__.update(datos)
        return obj
