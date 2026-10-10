# Core/Entities/Elementos/Abstractos/Condiciones/condicion.py
from abc import abstractmethod
from enum import Enum, auto

from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto
from Core.Entities.Elementos.elemento import Elemento


class Condicion(Elemento_Abstracto):
    """
    Base para condiciones serializables. Ya NO guarda un Callable
    (_evaluar) -- eso es lo que la hacía imposible de reconstruir.
    Cada subtipo concreto implementa evaluar() como método real, leyendo
    SOLO sus propios campos de instancia (umbral, tick_objetivo...),
    que ya viajan solos por el mecanismo genérico de
    Elemento.serializar()/deserializar() -- son datos planos (int,
    float, tuplas), nada que necesite un hook especial.

    'propietario' y 'ctx' se pasan en cada llamada a evaluar(), nunca se
    guardan como campo: así una condición sobre "mi propia humedad" o
    "mi propia temperatura" no necesita capturar una referencia al
    elemento dueño en un closure -- se la da quien la evalúa
    (Transformable.tick, que ya tiene 'self' porque es su propio
    comportamiento).

    IMPORTANTE: cada subtipo concreto (no "Condicion" a secas) debe
    registrarse en Core/Entities/Elementos/registry.py -- reconstruir
    una CondicionUmbralHumedad requiere que el registro sepa
    instanciar ESA clase, "Condicion" sola no basta.
    """

    class Modo(Enum):
        LOCAL = auto()
        DISTRIBUIDO = auto()

    def __init__(
        self,
        evento: str = None,
        nombre: str = None,
        id_elemento=None,
        **kwargs,
    ):
        super().__init__(tipo=type(self), id_elemento=id_elemento, **kwargs)
        self.activa: bool = False
        self.nombre = nombre

        if self.modo is Condicion.Modo.DISTRIBUIDO:
            if evento is None or nombre is None:
                raise ValueError("Condicion DISTRIBUIDA requiere 'evento' y 'nombre'.")
            Elemento.mundo.bus_eventos.suscribir(evento, self._on_evento)

    def _on_evento(self, *args, **kwargs) -> None:
        # Solo relevante en modo DISTRIBUIDO. 'propietario'/'ctx' no
        # existen aquí -- pendiente de resolver junto con el resto del
        # circuito distribuido, que sigue aparcado.
        self.activa = self.evaluar(*args, **kwargs)
        if self.activa:
            Elemento.mundo.bus_eventos.emitir(f"{self.nombre}{id(self)}")

    @abstractmethod
    def evaluar(self, propietario, ctx) -> bool: ...

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other) -> bool:
        return self is other
