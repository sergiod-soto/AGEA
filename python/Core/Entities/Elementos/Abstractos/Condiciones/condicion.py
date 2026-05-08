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
            self._suscribir_evento(evento, self._on_evento)

    def _on_evento(self, *args, **kwargs) -> None:
        self.activa = self._evaluar()
        if self.activa:
            Elemento.mundo.bus.emitir(f"condicion_activa_{id(self)}")

    def evaluar(self, contexto: dict = None) -> bool:
        return self._evaluar(contexto) if contexto else self._evaluar()
