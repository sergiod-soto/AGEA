# Core/Entities/Comportamiento/Interaccion/ingrediente.py


from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion


class Ingrediente(Interaccion):
    """
    Parametros:

    - recetas_de: list[int] = None   (id_elemento de cada Receta de la que forma parte)

    None equivale a "ninguna receta". Todos los elementos de un mismo tipo
    (p. ej. varias Agua) comparten las mismas recetas, pero cada uno guarda su
    propia lista. Se guardan IDs y no objetos Receta, por lo mismo que
    Agarrable: en un Sector no hay Mundo para resolverlos.
    """

    REQUIERE = {"recetas_de: list[int] = None"}
    ABSTRACTOS = {}

    def __init__(self, recetas_de: list[int] | None = None, **kwargs):
        super().__init__(**kwargs)
        self.recetas_de: list[int] = list(
            recetas_de or []
        )  # ID de las recetas a las que pertenece

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {
            "recetas_de": list(self.recetas_de),
        }
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        self.recetas_de = list(
            data["comportamientos"][__class__.__name__]["recetas_de"]
        )

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"ingrediente": {}}
        return datos

    def incluir_en_receta(self, id_receta: int) -> None:
        """Marca que este Elemento forma parte de la receta `id_receta`."""
        if id_receta not in self.recetas_de:
            self.recetas_de.append(id_receta)

    def parte_de_que_recetas(self) -> list[int]:
        """ids de las recetas de las que forma parte (copia)."""
        return list(self.recetas_de)

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return []

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento forma parte de una receta.

Atributos:
\trecetas_de: list[Receta]

Métodos:
\tincluir_en_receta(self, receta: Receta) -> None
\t--------------------------------------
\tSe define que este Elemento forma parte de dicha Receta.


\tparte_de_que_recetas(self) -> dict[str, Receta]
\t--------------------------------------
\tSe consulta de qué recetas este Elemento forma parte.
        """
