# Core/Entities/Elementos/Abstractos/Marcadores/Temporales/Estacion/estaciones.py

from Config.settings import (
    ID_ESTACIONES,
    ID_INVIERNO,
    ID_OTONO,
    ID_PRIMAVERA,
    ID_VERANO,
)
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.Estacion.estacion import (
    Estacion,
)
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.marcador_temporal import (
    Marcador_Temporal,
)
from Core.Entities.Elementos.Abstractos.Tiempo.reloj import Reloj


class Estaciones(Marcador_Temporal):
    """
    Lleva las estaciones: nada más. El progreso continuo del año lo lleva
    Ciclo_Anual.

    Su Reloj.Ciclo tiene 4 pasos (uno por estación) y avanza uno cada 3 meses.
    Al empezar cada paso el ciclo llama a _al_cambiar_estacion, que actualiza
    estacion_actual. Es una INSTANCIA de Invierno/Primavera/Verano/Otono (una
    de cada, creadas aquí con su ID): se compara con
    isinstance(x, Estaciones.Verano).

    La clasificación es GLOBAL y con un hemisferio fijo: NO la usa la radiación
    de cada celda (esa sale de latitud+declinación en sistema_atmosferico.py).
    """

    class Invierno(Estacion):
        def __init__(self, **kwargs):
            super().__init__(Estaciones.Invierno, ID_INVIERNO, **kwargs)

    class Primavera(Estacion):
        def __init__(self, **kwargs):
            super().__init__(Estaciones.Primavera, ID_PRIMAVERA, **kwargs)

    class Verano(Estacion):
        def __init__(self, **kwargs):
            super().__init__(Estaciones.Verano, ID_VERANO, **kwargs)

    class Otono(Estacion):
        def __init__(self, **kwargs):
            super().__init__(Estaciones.Otono, ID_OTONO, **kwargs)

    def __init__(self, mundo, estacion_inicial: int = 0, **kwargs):
        """estacion_inicial: índice en self.orden (0 = Invierno)."""
        super().__init__(Estaciones, ID_ESTACIONES, **kwargs)
        self.mundo = mundo
        # Las 4 instancias, en orden de año. El índice es el del ciclo.
        self.orden: list[Estacion] = [
            Estaciones.Invierno(),
            Estaciones.Primavera(),
            Estaciones.Verano(),
            Estaciones.Otono(),
        ]
        self.estacion_actual: Estacion = self.orden[estacion_inicial]
        self.ciclo: Reloj.Ciclo = self.mundo.reloj.agregar_ciclo(
            elemento=self,
            start=estacion_inicial,
            end=len(self.orden),
            paso=self.mundo.reloj.Mes(3),
            al_avanzar=self._al_cambiar_estacion,
        )

    def _al_cambiar_estacion(self, indice: int) -> None:
        """Callback del ciclo: se ejecuta al empezar cada estación."""
        self.estacion_actual = self.orden[indice]

    # --- serializar / deserializar (mismo patrón que Elemento_Simple) ---
    # Se guarda el ÍNDICE, no el objeto: las 4 instancias son siempre las mismas.

    def serializar_estacion_actual(self) -> int:
        return self.orden.index(self.estacion_actual)

    def deserializar_estacion_actual(self, indice: int) -> None:
        self.estacion_actual = self.orden[indice]

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["estacion_actual"] = self.serializar_estacion_actual()
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        # El ciclo es la fuente de verdad: Reloj.restaurar_estado ya lo dejó en
        # su sitio sin disparar el callback, así que se resincroniza desde él.
        # Lo guardado en data["estacion_actual"] solo se usa para avisar.
        esperada = self.orden[self.ciclo.tick_actual]
        if self.orden[data["estacion_actual"]] is not esperada:
            raise ValueError(
                "Estaciones: la estación guardada no coincide con el ciclo del reloj."
            )
        self.estacion_actual = esperada
