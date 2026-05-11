from typing import Callable
from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto
from Core.Entities.Elementos.elemento import Elemento


class Condicion(Elemento_Abstracto):
    """
    Ejemplo de uso:

    Condicion(
    evaluar=lambda: agua.temperatura_propia > 100,
    evento=f"temperatura_cambiada_{id(agua)}"
    )


    Parametros:

    - evaluar: Callable[..., bool]

    Metodos abstractos:

    -
    """

    def __init__(self, evaluar: Callable[..., bool], evento: str = None):
        super().__init__()
        self._evaluar = evaluar
        self.activa: bool = False
        if evento:
            Elemento.mundo.bus.suscribir(evento, self._on_evento)

    def _on_evento(self, *args, **kwargs) -> None:
        self.activa = self._evaluar(*args, **kwargs)
        if self.activa:
            Elemento.mundo.bus.emitir(f"condicion_activa_{id(self)}")

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other

    def evaluar(self, *args, **kwargs) -> bool:
        return self._evaluar(*args, **kwargs)
