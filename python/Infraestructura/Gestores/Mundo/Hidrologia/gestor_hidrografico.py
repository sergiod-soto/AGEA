# Infraestructura/Gestores/Mundo/Hidrologia/gestor_hidrografico.py
"""
gestor_hidrografico.py - Módulo desacoplado intersectores para la gestión
hidrográfica agregada (ríos, lagos y océanos).

Interfaz limpia de entrada/salida:
  - inicializar: carga el DAG inicial de hidrología y alturas.
  - preparar_tick (Fase 0): recibe las condiciones atmosféricas agregadas y extracciones.
  - avanzar_tick (Fase 1): computa en paralelo con los sectores el flujo por el DAG
                           y emite mutaciones discretas de terreno (changed_cells).
  - serializar / deserializar: persistencia desacoplada en snapshots.
"""

from __future__ import annotations
import asyncio
import logging
from typing import Optional

from Infraestructura.Gestores.Mundo.Hidrologia.modelos import (
    DatosAtmosferaHidro,
    ResultadoTickHidro,
)
from Infraestructura.Gestores.Mundo.Hidrologia.red_fluvial import RedFluvial

logger = logging.getLogger(__name__)


class GestorHidrografico:
    """
    Gestor del ciclo hidrológico mundial desacoplado de gRPC y de los internos de Mundo.
    Puede ejecutarse como corrutina en Fase 1 o escalarse a proceso worker independiente.
    """

    def __init__(self):
        self.red_fluvial: RedFluvial = RedFluvial()
        self._datos_atmosfera_pendientes: dict[tuple[int, int], DatosAtmosferaHidro] = {}
        self._extracciones_pendientes: dict[int, float] = {}
        self._inicializado: bool = False
        self._lock = asyncio.Lock()

    @property
    def inicializado(self) -> bool:
        return self._inicializado

    def inicializar(
        self,
        red: dict,
        hidrologia: dict[tuple[int, int], dict],
        alturas: dict[tuple[int, int], int],
        suelos_originales: Optional[dict[tuple[int, int], str]] = None,
    ) -> None:
        """
        Inicializa el grafo de ríos y lagos a partir de los datos de generación o snapshot.
        """
        self.red_fluvial.inicializar_desde_red(
            red=red,
            hidrologia=hidrologia,
            alturas=alturas,
            suelos_originales=suelos_originales,
        )
        self._inicializado = True
        logger.info("GestorHidrografico inicializado correctamente.")

    def preparar_tick(
        self,
        tick_id: int,
        datos_atmosfera: dict[tuple[int, int], DatosAtmosferaHidro],
        extracciones: Optional[dict[int, float]] = None,
    ) -> None:
        """
        Fase 0: Prepara los datos de entrada para el tick actual.
        Recibe la atmósfera agregada (precipitación, evaporación Dalton potencial)
        y extracciones de agua por parte de bots u otras entidades.
        """
        self._datos_atmosfera_pendientes = dict(datos_atmosfera)
        self._extracciones_pendientes = dict(extracciones or {})

    async def avanzar_tick(self, tick_id: int) -> ResultadoTickHidro:
        """
        Fase 1: Ejecuta la simulación fluvial del tick en paralelo con los sectores.
        Devuelve el ResultadoTickHidro con las mutaciones discretas (changed_cells)
        para ser consolidadas en Fase 2.
        """
        async with self._lock:
            # Si no hay red fluvial cargada, devuelve un delta vacío sin fallar
            if not self._inicializado:
                return ResultadoTickHidro(tick_id=tick_id)

            resultado = self.red_fluvial.simular_paso(
                tick_id=tick_id,
                datos_atmosfera=self._datos_atmosfera_pendientes,
                extracciones=self._extracciones_pendientes,
            )

            # Limpiar datos del tick procesado
            self._datos_atmosfera_pendientes.clear()
            self._extracciones_pendientes.clear()

            return resultado

    def invalidar_seccion(self, tipo: str, id_elem: int) -> None:
        """Notifica cambios en el terreno para recálculo dinámico de cauce/cuenca."""
        self.red_fluvial.invalidar_seccion(tipo, id_elem)

    def serializar(self) -> dict:
        """Serializa el estado del gestor para snapshots."""
        return {
            "inicializado": self._inicializado,
            "red_fluvial": self.red_fluvial.serializar(),
        }

    def deserializar(self, datos: dict) -> None:
        """Restaura el estado del gestor desde un snapshot."""
        self._inicializado = bool(datos.get("inicializado", False))
        if "red_fluvial" in datos:
            self.red_fluvial.deserializar(datos["red_fluvial"])
