# Core/Entities/Comportamiento/Material/erosionable.py

from abc import abstractmethod

from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.Abstractos.Acciones.accion import Accion
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class Erosionable(Material):
    """
    Parametros:

    - condiciones_erosion: list[tuple[list[Condicion], float]]
    - durabilidad_max_erosion: float
    - durabilidad_actual_erosion: float = None

    Metodos abstractos:

    - erosionar(self, cantidad: float)
    - _destruir(self, efecto: Accion)
    """

    REQUIERE = {
        "condiciones_erosion: list[tuple[list[Condicion], float]]",
        "durabilidad_max_erosion: float",
    }
    ABSTRACTOS = {
        "def erosionar(self, cantidad: float)",
        "def _destruir(self, efecto: Accion)",
    }

    def __init__(
        self,
        durabilidad_max_erosion: float,
        condiciones_erosion: list[tuple[list[Condicion], float]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.durabilidad_max_erosion = durabilidad_max_erosion
        self.condiciones_erosion = condiciones_erosion or []
        self.durabilidad_actual_erosion = durabilidad_max_erosion

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {
            "durabilidad_max_erosion": self.durabilidad_max_erosion,
            "durabilidad_actual_erosion": self.durabilidad_actual_erosion,
            "condiciones_erosion": self.serializar_condiciones_erosion(),
        }
        return datos

    def serializar_condiciones_erosion(self) -> list:
        """[(lista de Condicion, cantidad)] -> [[[dict, ...], cantidad], ...].
        Cada Condicion es un Elemento, así que se guarda con su serializar()."""
        return [
            [[c.serializar() for c in condiciones], cantidad]
            for condiciones, cantidad in self.condiciones_erosion
        ]

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"erosionable": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        seccion = data["comportamientos"][__class__.__name__]
        self.durabilidad_max_erosion = seccion["durabilidad_max_erosion"]
        self.durabilidad_actual_erosion = seccion["durabilidad_actual_erosion"]
        self.deserializar_condiciones_erosion(seccion["condiciones_erosion"], mundo)

    def deserializar_condiciones_erosion(self, valor: list, mundo=None) -> None:
        # Import diferido: el registry importa todos los comportamientos, y
        # un import arriba sería circular.
        from Core.Entities.Elementos.registry import reconstruir_elemento

        self.condiciones_erosion = [
            ([reconstruir_elemento(c, mundo) for c in condiciones], cantidad)
            for condiciones, cantidad in valor
        ]

    @classmethod
    def _campos_internos(cls):
        return {"durabilidad_actual_erosion"}

    def tick_comportamiento(self, ctx) -> None:
        # TODO: comporbar que funciona correctamente y no machaca ningun otro tick()
        for condiciones, cantidad in self.condiciones_erosion:
            if all(c.evaluar() for c in condiciones):
                self.erosionar(cantidad)

    @abstractmethod
    def erosionar(self, cantidad: float): ...

    @abstractmethod
    def _destruir(self, efecto: Accion): ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "condiciones_erosion",
            "durabilidad_max_erosion",
            "durabilidad_actual_erosion",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•Indica que el Elemento puede ser erosionado, frotando, por ejemplo.

Atributos:
\tcondiciones_erosion: list[tuple[list[Condicion], float]]
\tdurabilidad_max_erosion: float
\tdurabilidad_actual_erosion: float = None

Métodos:
\ttick(self) -> None
\t--------------------------------------
\tComputa el siguiente tick.

\t@abstractmethod erosionar(self, cantidad: float)
\t--------------------------------------
\tEjecuta un tick de erosión.

\t@abstractmethod _destruir(self, efecto: Accion)
\t--------------------------------------
\tRealiza una accion al Elemento ser destruido por erosión.
        """
