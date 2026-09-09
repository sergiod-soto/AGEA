# Core/Entities/Elementos/elemento_test.py

from Core.Entities.Comportamiento.Fisico.peso import Peso
from Core.Entities.Comportamiento.comportamiento_test import Comportamiento_Test
from Core.Entities.Elementos.Simples.elemento_simple import Elemento_Simple
from Core.Entities.Comportamiento.comportamiento import Comportamiento

comportamientos = Comportamiento.declarar_comportamientos(
    Comportamiento_Test,
    Peso,
)


class Elemento_Test(Elemento_Simple, comportamientos):

    def __init__(
        self,
        casilla: tuple[int, int],
        id_elemento,
        # Peso:
        peso: float,
        **kwargs
    ):
        if peso < 0:
            peso = 0
        super().__init__(
            tipo=Elemento_Test,
            id_elemento=id_elemento,
            tamanho=1,
            casilla=casilla,
            capa=1,
            # Peso:
            peso=peso,
            **kwargs
        )

    def representacion(self, modo: str, incluir: list[str] = None) -> dict:
        serializacion_simple = self.serializar_elemento_simple(modo=modo)

        campos = {}
        campos["elemento"] = {
            "tamanho": self.serializar_tamanho(),
            "casilla": self.serializar_casilla(),
            "rotacion": self.serializar_rotacion(),
        }
        campos["elemento"].update(serializacion_simple)

        campos["comportamientos"] = {
            cls.__name__: self.serializar(cls, modo=modo)
            for cls in self._get_comportamientos()
            if cls.__name__ in incluir
        }

        return campos

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        # Todos los parámetros obligatorios de __init__, en el mismo
        # orden que aparecen ahí (facilita comparar visualmente si
        # cambia la firma del constructor).
        return [
            Peso.campos_para_creacion(),
        ]
