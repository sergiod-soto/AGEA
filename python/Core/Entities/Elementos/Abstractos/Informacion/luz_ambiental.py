# Core/Entities/Elementos/Abstractos/Informacion/luz_ambiental.py

from Config.parametros_simulacion import RADIACION_MAXIMA
from Config.settings import ID_LUZ_AMBIENTAL
from Core.Entities.Elementos.Abstractos.Informacion.informacion import Informacion


class Luz_Ambiental(Informacion):
    """
    Intensidad de la luz ambiental en una posición, en [0, 1].

    No calcula astronomía propia: toma la radiación de la Celda_Atmosfera de la
    posición (que ya incluye hora, latitud, declinación y noche) y le suma la
    luna. Una sola fuente de verdad para el día y la estación.

      luz_solar = radiacion / RADIACION_MAXIMA            (0 de noche, 1 a pleno sol)
      luz_luna  = FACTOR_LUNA * intensidad_luna * (1 - luz_solar)
      resultado = (luz_solar + luz_luna) * (1 - nubosidad)

    La luna entra multiplicada por (1 - luz_solar): aporta cuando el sol aún no
    ilumina y se apaga solo de día, sin mirar la hora. Pura: no necesita Mundo,
    así que sirve igual dentro de un Sector.
    """

    # Una luna llena vale como máximo esta fracción de la luz solar. 0.2 sale
    # de la escala del esbozo anterior (sol 0-100, luna 0-20).
    FACTOR_LUNA = 0.2

    def __init__(self, **kwargs):
        super().__init__(Luz_Ambiental, ID_LUZ_AMBIENTAL, **kwargs)

    @staticmethod
    def _validar_unidad(valor: float, nombre: str) -> float:
        # `not (...)` para rechazar también NaN.
        if not 0.0 <= valor <= 1.0:
            raise ValueError(f"{nombre} debe estar en [0, 1]; recibido {valor!r}")
        return valor

    def get_intensidad(
        self, radiacion: float, intensidad_luna: float, nubosidad: float = 0.0
    ) -> float:
        """
        radiacion: W/m² de la celda de atmósfera de la posición.
        intensidad_luna: [0, 1] (Ciclo_Lunar.intensidad_para_progreso).
        nubosidad: [0, 1]; 0 hasta que exista el sistema de nubes.
        """
        self._validar_unidad(intensidad_luna, "intensidad_luna")
        self._validar_unidad(nubosidad, "nubosidad")
        # La radiación puede pasarse de RADIACION_MAXIMA por redondeo: se recorta.
        luz_solar = min(1.0, max(0.0, radiacion / RADIACION_MAXIMA))
        luz_luna = self.FACTOR_LUNA * intensidad_luna * (1.0 - luz_solar)
        return (luz_solar + luz_luna) * (1.0 - nubosidad)
