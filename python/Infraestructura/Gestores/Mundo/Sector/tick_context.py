# Infraestructura/Gestores/Mundo/Sector/tick_context.py
"""
Contexto que se pasa a tick() de cada elemento durante la computación
de un Sector.

Dos responsabilidades, deliberadamente separadas:

    1. LECTURA — get_celda()/en_region_propia(). Siempre devuelven el estado
        con el que empezó el tick (instantánea recibida en el delta de entrada
        + ghost zone de los vecinos), nunca el resultado de una mutación ya
        pedida por otro elemento en este mismo tick. Es una decisión de diseño
        explícita: prioriza determinismo y simplicidad (el resultado de un
        tick no depende del orden en que se computan los elementos dentro del
        sector) por encima de permitir "ver" cambios a medias dentro del tick.

    2. ESCRITURA — guardar_elemento()/eliminar_elemento()/mover_elemento().
        No aplican nada: acumulan la petición en una lista. Sector, al
        terminar de ejecutar tick() de todos sus elementos, usa
        obtener_mutaciones() y las resuelve él mismo sobre su copia de
        trabajo (Sector._resolver_mutaciones). Los cambios resultantes viajan
        a Logica_Mundo como changed_cells.


Por qué escritura diferida: si tick() aplicase los cambios al momento, el
resultado dependería del orden en que se computan los elementos.
"""

from dataclasses import dataclass
import json
from typing import Any, Optional

from Core.Entities.Mundo.Funciones.tipo_slot import tipo_slot_de
from Infraestructura.Gestores.Mundo.Sector.escala_atmosfera import (
    pos_terreno_a_atmosfera,
)
from Infraestructura.Gestores.Mundo.Sector.mutaciones import (
    CrearElemento,
    EliminarElemento,
    Evaporar,
    MoverElemento,
    Mutacion,
)


@dataclass(frozen=True)
class EventoPedido:
    """Evento pedido durante el tick. El payload ya va serializado (JSON): así
    un valor no serializable falla en emitir_evento, en el elemento culpable."""

    tipo: str
    payload: bytes
    agrupable: bool = False


class TickContext:

    def __init__(
        self,
        celdas_inicio_tick,
        ghost: dict,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        atmosfera=None,  # CeldaAtmosferaStore propio del Sector
        ghost_atmosfera: Optional[dict] = None,
        escala_atmosfera: int = 1,
        margen_ghost: int = 0,
        tick_id: int = 0,
    ):
        self._celdas = celdas_inicio_tick
        self._ghost = ghost
        self._x0, self._y0, self._x1, self._y1 = x0, y0, x1, y1
        self._atmosfera = atmosfera
        self._ghost_atmosfera = ghost_atmosfera or {}
        self._escala_atmosfera = escala_atmosfera
        self._margen_ghost = margen_ghost
        self.tick_id = tick_id
        self._mutaciones: list[Mutacion] = []
        self._contador_nuevos = 0
        self._eventos: list[EventoPedido] = []

    # ─────────────────────────────────────────
    #  Lectura (siempre estado de inicio de tick)
    # ─────────────────────────────────────────

    def get_celda(self, x: int, y: int) -> Optional[Any]:
        """Devuelve la celda en (x, y): de la región propia si cae dentro
        de los límites del sector, o de la ghost zone si es de un vecino.
        None si no hay nada en esa celda."""
        if self.en_region_propia(x, y):
            return self._celdas.get(x, y)
        return self._ghost.get((x, y))

    def get_atmosfera(self, x: int, y: int):
        """
        Devuelve la Celda_Atmosfera que cubre la posición de TERRENO (x, y)
        -- quien llama no necesita conocer ATMOSFERA_ESCALA, la conversión
        se hace aquí.

        Devuelve la celda VIVA (no una copia): en compute_tick, tick() de
        los elementos corre ANTES de _avanzar_atmosfera, así que esto ya
        es consistente con leer "estado de inicio de tick" sin necesidad
        de congelar nada. Solo para LECTURA desde tick() de los elementos.
        Las cachés de la celda las mantiene únicamente Sector.

        None si la posición no está en la malla propia del Sector.

        LIMITACIÓN CONOCIDA, sin resolver a propósito: la ghost zone de
        atmósfera (self._ghost_atmosfera) solo tiene margen de 1 bloque,
        y además guarda AtmosphereCell (proto), no Celda_Atmosfera -- un
        tipo distinto al que se devuelve para la malla propia. Hoy no hace
        falta resolverlo: el único consumidor (Suelo.tick, vía
        Transformable) siempre consulta su PROPIA posición, que por
        definición cae dentro de la malla propia del Sector, nunca en la
        ghost zone. Si en el futuro algo (p.ej. un bot con visión) necesita
        consultar atmósfera fuera de su propio bloque, esto habrá que
        revisarlo: o se unifica el tipo devuelto, o se documenta que
        get_atmosfera solo sirve para "mi propia celda".
        """
        if self._atmosfera is None:
            return None
        return self._atmosfera.get(
            *pos_terreno_a_atmosfera(x, y, self._escala_atmosfera)
        )

    def celdas_en_radio(self, x: int, y: int, radio: int) -> list:
        """
        Devuelve las celdas de terreno alrededor de (x, y) usando distancia
        Chebyshev: max(|dx|, |dy|) <= radio. Esto genera un CUADRADO de
        lado (2*radio + 1) centrado en (x, y), no un círculo -- se eligió
        así por ser más barato (sin raíces cuadradas) y porque el radio
        real de uso (CondicionVecinoCercano, etc.) es "pocas casillas": la
        diferencia frente a un círculo no importa en la práctica.

        Reutiliza get_celda, así que respeta las mismas reglas de lectura
        que el resto del contexto: incluye tanto la región propia como la
        ghost zone del sector, y usa el estado de inicio de tick.

        Se filtran las posiciones vacías (get_celda devuelve None): el
        resultado solo contiene celdas que existen.
        """
        if radio < 0:
            raise ValueError("radio no puede ser negativo")

        if radio > self._margen_ghost:
            # Más allá del margen de la ghost zone las celdas de otro Sector no
            # existen aquí: el resultado dependería de cómo se reparte el mundo
            # en Sectores (distinto en local y en AWS). Se falla en vez de
            # devolver menos celdas en silencio.
            raise ValueError(
                f"radio {radio} supera el margen de la ghost zone "
                f"({self._margen_ghost}); subir MAX_VISION_DISTANCE."
            )

        resultado = []
        for dx in range(-radio, radio + 1):
            for dy in range(-radio, radio + 1):
                celda = self.get_celda(x + dx, y + dy)
                if celda is not None:
                    resultado.append(celda)
        return resultado

    def en_region_propia(self, x: int, y: int) -> bool:
        return self._x0 <= x < self._x1 and self._y0 <= y < self._y1

    # ─────────────────────────────────────────
    #  Escritura (diferida — solo se acumula, no se aplica aquí)
    # ─────────────────────────────────────────

    def guardar_elemento(
        self,
        pos: tuple[int, int],
        elemento: Any,
        bot_id: Optional[int] = None,
    ) -> str:
        # El slot sale de la CLASE (igual que en Logica): una sola fuente de
        # verdad, para que nadie pueda poner un suelo en "resto".
        tipo_slot = tipo_slot_de(elemento)
        marcador = f"nuevo_{self._contador_nuevos}"
        self._contador_nuevos += 1
        self._mutaciones.append(
            CrearElemento(
                marcador_local=marcador,
                pos=pos,
                tipo_slot=tipo_slot,
                elemento=elemento,
                bot_id=bot_id,
            )
        )
        return marcador

    def mover_elemento(
        self,
        id_elemento: int,
        pos_origen: tuple[int, int],
        pos_destino: tuple[int, int],
        bot_id: Optional[int] = None,
    ) -> None:
        self._mutaciones.append(
            MoverElemento(
                id_elemento=id_elemento,
                pos_origen=pos_origen,
                pos_destino=pos_destino,
                bot_id=bot_id,
            )
        )

    def eliminar_elemento(
        self,
        id_elemento: int,
        pos: tuple[int, int],
        bot_id: Optional[int] = None,
    ) -> None:
        self._mutaciones.append(
            EliminarElemento(
                id_elemento=id_elemento,
                pos=pos,
                bot_id=bot_id,
            )
        )

    def evaporar(self, pos: tuple[int, int], kg_por_m2: float) -> None:
        """
        Pide pasar `kg_por_m2` de agua de la casilla `pos` al aire. Escritura
        diferida: aquí solo se acumula; el Sector la aplica a la humedad de la
        Celda_Atmosfera antes de _avanzar_atmosfera. Nunca escribas la
        atmósfera desde tick(): get_atmosfera es solo para LECTURA.

        ValueError si no es un número finito >= 0 (fallar aquí señala al
        elemento culpable; en el Sector sería un fallo fatal anónimo).
        """
        if not (kg_por_m2 >= 0.0) or kg_por_m2 == float("inf"):
            raise ValueError(
                f"kg_por_m2 debe ser finito y >= 0 (recibido {kg_por_m2})."
            )
        self._mutaciones.append(Evaporar(pos=pos, kg_por_m2=kg_por_m2))

    def emitir_evento(
        self, tipo: str, *args, agrupable: bool = False, **kwargs
    ) -> None:
        """
        Pide emitir un evento en el bus de Logica_Mundo. Escritura diferida,
        como las mutaciones: aquí solo se acumula; el Sector lo envía en el
        delta y Logica lo emite DESPUÉS de aplicar las celdas del tick.

        args/kwargs viajan por red como JSON: solo números, strings, bools,
        None, listas y dicts (una tupla llega como lista). TypeError si no.
        agrupable: reservado. True = "estado actual", el último valor del mismo
        `tipo` sustituye a los anteriores. Hoy se ignora.
        """
        payload = json.dumps({"args": list(args), "kwargs": kwargs}).encode()
        self._eventos.append(EventoPedido(tipo, payload, agrupable))

    # ─────────────────────────────────────────
    #  Cierre del tick
    # ─────────────────────────────────────────

    def obtener_mutaciones(self) -> list[Mutacion]:
        """Llamado por Sector al terminar de ejecutar tick() de todos sus
        elementos, para construir el TickDelta que se envía a Logica_Mundo."""
        return self._mutaciones

    def obtener_eventos(self) -> list[EventoPedido]:
        """Llamado por Sector al acabar el tick, junto a obtener_mutaciones."""
        return self._eventos
