# Core/Entities/Comportamiento/Terreno/acuoso.py

from Config.parametros_simulacion import (
    ALTURA_CAPA_AIRE,
    EVAPORACION_COEF_BASE,
    EVAPORACION_COEF_VIENTO,
    SEGUNDOS_SIMULADOS_TICK,
)
from Core.Entities.Comportamiento.Terreno.terreno import Terreno
from Core.Fisica.termodinamica import densidad_vapor_saturacion


class Acuoso(Terreno):
    """
    Masa de agua (río, océano...). Evapora agua hacia la celda de atmósfera
    que cubre su casilla. La física (humedad y enfriamiento por calor latente)
    la aplica el Sector, no este comportamiento: aquí solo se decide CUÁNTA agua.
    """

    REQUIERE = {}
    ABSTRACTOS = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def tick_comportamiento(self, ctx) -> None:
        """
        Pide evaporar con un modelo tipo Dalton:

            E = (A + B·v) · (ρ_sat(T_agua) − ρ_vapor)        [kg/(m²·s)]

        - T_agua = temperatura del suelo de la celda (el agua es suelo aquí).
        - ρ_vapor = humedad absoluta actual del aire; v = viento de la celda.
        - Se lee la celda con ctx.get_atmosfera (solo LECTURA, estado de inicio
          de tick) y se escribe con ctx.evaporar (diferido y aditivo): el
          resultado no depende del orden de los elementos.

        TOPE por déficit del aire: lo evaporado nunca supera lo que falta para
        saturar la capa de aire (ρ_sat(T_aire) − ρ_vapor)·ALTURA_CAPA_AIRE. Sin
        él, un tick podría pasar de la saturación y Humedad_Relativa lo
        ocultaría recortando a 100 %.
        """
        celda = ctx.get_atmosfera(*self.casilla)
        if celda is None:
            # Fatal: un agua sin celda de atmósfera indica un mundo mal
            # generado o un LoadState incompleto. Seguir ocultaría la
            # divergencia; el Sector registra el elemento y aborta el tick.
            raise RuntimeError(
                f"{type(self).__name__} en {self.casilla}: sin Celda_Atmosfera."
            )

        t_agua = celda.temperatura.valor_suelo
        t_aire = celda.temperatura.valor
        if t_agua <= 0 or t_aire <= 0:
            # Fatal, igual que la celda ausente: temperatura <= 0 K es un
            # estado imposible. Duplica la comprobación de
            # Temperatura.actualizar a propósito: aquí se detecta ANTES de
            # evaluar la saturación (que divide por la temperatura).
            raise ValueError(
                f"{type(self).__name__} en {self.casilla}: temperatura <= 0 K "
                f"(agua {t_agua}, aire {t_aire})."
            )

        vapor = celda.humedad_absoluta.valor
        deficit_agua = densidad_vapor_saturacion(t_agua) - vapor
        if deficit_agua <= 0:
            return  # el aire ya tiene más vapor que el que sostendría el agua

        velocidad_transferencia = (
            EVAPORACION_COEF_BASE + EVAPORACION_COEF_VIENTO * celda.viento.intensidad
        )
        kg_por_m2 = velocidad_transferencia * deficit_agua * SEGUNDOS_SIMULADOS_TICK

        capacidad_aire = max(0.0, densidad_vapor_saturacion(t_aire) - vapor)
        kg_por_m2 = min(kg_por_m2, capacidad_aire * ALTURA_CAPA_AIRE)

        if kg_por_m2 > 0.0:
            ctx.evaporar(self.casilla, kg_por_m2)

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"acuoso": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"acuoso": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
