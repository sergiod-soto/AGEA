# Core/Entities/Mundo/Celda/celda_atmosfera.py
from vectors import Vector2

from Core.Entities.Elementos.Abstractos.Bioma.bioma import Bioma


class Celda_Atmosfera:

    class _Viento:
        def __init__(self, intensidad: float, direccion: Vector2) -> None:
            self.intensidad = intensidad
            self.direccion = direccion

    def __init__(
        self,
        posicion: tuple[int, int],
        resistencia_viento: float,
        direccion_preferente_viento: Vector2,
        fuerza_viento: Vector2,
        bioma: Bioma,
    ) -> None:
        # variables a simular
        self.posicion = posicion
        self.temperatura: float = 20.0
        self.humedad_absoluta: float = 0.0
        self.presion: float = 1000.0
        self.radiacion: float = 0.0
        self.viento = self._Viento(0.0, Vector2(0, 0))

        # propiedades relacionados al terreno:
        self.resistencia_viento = resistencia_viento  # 0 = libre, 1 = bloqueado
        self.direccion_preferente_viento = (
            direccion_preferente_viento  # dirección preferente opcional
        )
        self.fuerza_viento = fuerza_viento  # fuerza artificial opcional
        self.bioma = bioma
