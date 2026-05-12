from typing import Callable
from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto
from Core.Entities.Elementos.elemento import Elemento


class Condicion(Elemento_Abstracto):
    """
    Una Condicion puede ser trigger.

    Ejemplo de uso:

    Condicion(
    evaluar=lambda: agua.temperatura_propia > 100,
    evento=f"temperatura_cambiada_{id(agua)}"
    )


    Parametros:

    - evaluar: Callable[..., bool]
    - evento: str = None

    Metodos abstractos:

    -
    """

    def __init__(
        self,
        evaluar: Callable[..., bool],
        evento: str = None,
        nombre: str = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._evaluar = evaluar
        self.activa: bool = False
        self.nombre = nombre
        if evento:
            Elemento.mundo.bus.suscribir(evento, self._on_evento)

    def _on_evento(self, *args, **kwargs) -> None:
        if self.nombre is None:
            raise Exception("Evento trigger sin nombre")

        self.activa = self._evaluar(*args, **kwargs)
        if self.activa:
            Elemento.mundo.bus.emitir(f"{self.nombre}{id(self)}")

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other

    def evaluar(self, *args, **kwargs) -> bool:
        return self._evaluar(*args, **kwargs)
