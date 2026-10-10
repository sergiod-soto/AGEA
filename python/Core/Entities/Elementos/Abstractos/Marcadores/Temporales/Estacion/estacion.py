# Core/Entities/Elementos/Abstractos/Marcadores/Temporales/Estacion/estacion.py

from Config.settings import ID_ESTACION
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.marcador_temporal import (
    Marcador_Temporal,
)
from Core.Entities.Elementos.Abstractos.Tiempo.reloj import Reloj


class Estacion(Marcador_Temporal):
    """
    Dueña del Reloj.Ciclo anual + selector de la estación categórica
    activa. Solo debe existir UNA instancia de Estacion en todo el
    mundo.

    Verano/Invierno/Primavera/Otono (mismo paquete) heredan de Estacion
    solo para servir de ETIQUETA distinguible por tipo -- NUNCA se
    instancian, se usan como la propia clase (p.ej. "estacion_actual is
    Verano"), nunca como Verano().

    IMPORTANTE: esta clasificación es GLOBAL y usa una convención de
    hemisferio fija en todo el mapa -- NO la usa la radiación real de
    cada celda de atmósfera (esa se calcula por latitud+declinación en
    sistema_atmosferico.py, que sí es correcta por hemisferio).
    Esto es solo una etiqueta para otros sistemas (vegetación, eventos...)
    que necesiten saber "en qué estación estamos" de forma simple.
    Si alguno de esos sistemas resulta necesitar la versión
    correcta por hemisferio, esto habrá que revisarlo entonces.

    Requiere que los 3 bugs señalados en reloj.py estén corregidos
    (Reloj.ciclos debe arrancar vacío, Mundo.reloj debe ser una
    instancia Reloj() no la clase, y self.mundo.reloj.Anho(1) necesita
    esa instancia) -- sin eso, self.mundo.reloj.agregar_ciclo(...)
    revienta.
    """

    def __init__(self, mundo, **kwargs):
        super().__init__(Estacion, ID_ESTACION, **kwargs)
        self.mundo = mundo
        self.ciclo: Reloj.Ciclo = self.mundo.reloj.agregar_ciclo(
            Estacion, self.mundo.reloj.Anho(1)
        )

    @staticmethod
    def _orden_estaciones() -> list:
        # Import diferido: evita import circular (cada subclase importa
        # Estacion desde este mismo módulo).
        from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.Estacion.primavera import (
            Primavera,
        )
        from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.Estacion.verano import (
            Verano,
        )
        from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.Estacion.otono import (
            Otono,
        )
        from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.Estacion.invierno import (
            Invierno,
        )

        return [Primavera, Verano, Otono, Invierno]

    def get_estacion_actual(self) -> type:
        """
        Devuelve la CLASE (Primavera/Verano/Otono/Invierno) activa
        ahora mismo, según self.ciclo.tick_actual. No instancia nada.

        Asume las 4 estaciones con la MISMA duración (un cuarto del
        año) -- si hiciera falta que duraran distinto (calendario real,
        p. ej.), este es el único sitio que cambiaría.

        NOTA: usa self.ciclo._end (atributo "privado" de Reloj.Ciclo)
        porque Reloj.Ciclo no expone la duración total como propiedad
        pública -- mejora aparte sería añadir un `duracion` público a
        Reloj.Ciclo en vez de leer un atributo con guion bajo desde
        fuera de su clase.
        """
        estaciones = self._orden_estaciones()
        duracion_anual = self.ciclo._end
        duracion_estacion = duracion_anual / len(estaciones)
        indice = min(
            int(self.ciclo.tick_actual // duracion_estacion), len(estaciones) - 1
        )
        return estaciones[indice]
