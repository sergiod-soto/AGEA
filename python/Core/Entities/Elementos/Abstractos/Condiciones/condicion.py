# Core/Entities/Elementos/Abstractos/Condiciones/condicion.py
from enum import Enum, auto
from typing import Callable

from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto
from Core.Entities.Elementos.elemento import Elemento


class Condicion(Elemento_Abstracto):
    """
    Modo LOCAL: evaluar() se llama a mano por quien posee la Condicion
    (p. ej. Transformable.tick), en el propio tick del elemento. No
    toca el bus, no depende de Elemento.mundo -- funciona igual dentro
    de un proceso de Sector que en Logica_Mundo. Es el modo que
    necesita Suelo (y cualquier elemento cuya transformación se
    resuelva vía TickContext).

    Modo DISTRIBUIDO: para condiciones que dependen de estado que un
    Sector no puede ver por sí mismo (candidato: ElementoGlobal).
    Requiere Elemento.mundo, que SOLO existe en el proceso de
    Logica_Mundo -- construir una Condicion en este modo dentro de un
    Sector es un error de programación, no un caso de uso válido.

    IMPORTANTE: el circuito que lleva el evento de entrada desde un
    Sector hasta Logica_Mundo, y el de salida de vuelta al Sector
    (Sector -> Gestor -> Logica -> Gestor -> Sector), NO EXISTE
    todavía -- ver nota de diseño pendiente. Este modo hoy solo sirve
    para condiciones que se evalúan y disparan enteramente dentro del
    proceso de Logica_Mundo, sin necesidad de ese circuito.
    """

    class Modo(Enum):
        LOCAL = auto()
        DISTRIBUIDO = auto()

    def __init__(
        self,
        evaluar: Callable[..., bool],
        modo: "Condicion.Modo" = None,
        evento: str = None,
        nombre: str = None,
        **kwargs,
    ):
        super().__init__(Condicion, **kwargs)
        self._evaluar = evaluar
        self.modo = modo or Condicion.Modo.LOCAL
        self.activa: bool = False
        self.nombre = nombre

        if self.modo is Condicion.Modo.DISTRIBUIDO:
            if evento is None or nombre is None:
                raise ValueError(
                    "Condicion en modo DISTRIBUIDO requiere 'evento' y 'nombre'."
                )
            Elemento.mundo.bus_eventos.suscribir(evento, self._on_evento)

    def _on_evento(self, *args, **kwargs) -> None:
        """Solo relevante en modo DISTRIBUIDO -- el bus llama aquí
        cuando llega el evento de entrada al que nos suscribimos."""
        self.activa = self._evaluar(*args, **kwargs)
        if self.activa:
            Elemento.mundo.bus_eventos.emitir(f"{self.nombre}{id(self)}")

    def evaluar(self, *args, **kwargs) -> bool:
        """Uso directo (modo LOCAL): quien posee la Condicion la llama
        explícitamente, sin pasar por el bus."""
        self.activa = self._evaluar(*args, **kwargs)
        return self.activa

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other) -> bool:
        return self is other
