# Core/Entities/Elementos/registry.py
"""
registry.py — Mapa nombre de clase → clase, para reconstruir
elementos serializados (ver Elemento.serializar/deserializar).

Para añadir un elemento nuevo: importarlo aquí y añadirlo a ELEMENTOS.
"""

from typing import TYPE_CHECKING

from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Entities.Comportamiento.registry import COMPORTAMIENTOS

from Core.Entities.Elementos.Abstractos.Acciones.accion import Accion
from Core.Entities.Elementos.Abstractos.Acciones.mezclar import Mezclar
from Core.Entities.Elementos.Abstractos.Condiciones.Condiciones_Atmosfericas.condicion_umbral_humedad import (
    CondicionUmbralHumedad,
)
from Core.Entities.Elementos.Abstractos.Condiciones.Condiciones_Fisicas.condicion_temperatura import (
    CondicionTemperatura,
)
from Core.Entities.Elementos.Abstractos.Condiciones.Condiciones_Fisicas.condicion_vecino_cercano import (
    CondicionVecinoCercano,
)
from Core.Entities.Elementos.Abstractos.Condiciones.Condiciones_Logicas.condicion_and import (
    CondicionAnd,
)
from Core.Entities.Elementos.Abstractos.Condiciones.Condiciones_Logicas.condicion_or import (
    CondicionOr,
)
from Core.Entities.Elementos.Abstractos.Condiciones.Condiciones_Temporales.condicion_tick_objetivo import (
    CondicionTickObjetivo,
)
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.Estacion.estacion import (
    Estacion,
)
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.Estacion.estaciones import (
    Estaciones,
)
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.ciclo_anual import (
    Ciclo_Anual,
)
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.ciclo_solar import (
    Ciclo_Solar,
)
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Derivado.humedad_relativa import (
    Humedad_Relativa,
)
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.humedad_absoluta import (
    Humedad_Absoluta,
)
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.presion import (
    Presion,
)
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.temperatura_atmosferica import (
    TemperaturaAtmosferica,
)
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.viento import (
    Viento,
)
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
    Sistema_Atmosferico,
)
from Core.Entities.Elementos.Abstractos.Tiempo.reloj import Reloj
from Core.Entities.Elementos.Simples.elemento_simple import Elemento_Simple
from Core.Entities.Mundo.Suelo.suelo import Suelo
from Core.Entities.Mundo.Suelo.suelo_arena import Suelo_Arena
from Core.Entities.Mundo.Suelo.suelo_barro import Suelo_Barro
from Core.Entities.Mundo.Suelo.suelo_cesped import Suelo_Cesped
from Core.Entities.Mundo.Suelo.suelo_grava import Suelo_Grava
from Core.Entities.Mundo.Suelo.suelo_hielo import Suelo_Hielo
from Core.Entities.Mundo.Suelo.suelo_oceano import Suelo_Oceano
from Core.Entities.Mundo.Suelo.suelo_piedra import Suelo_Piedra
from Core.Entities.Mundo.Suelo.suelo_tierra import Suelo_Tierra
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion
from Core.Entities.Elementos.Abstractos.Informacion.informacion import Informacion
from Core.Entities.Elementos.Abstractos.Informacion.raycast import Raycast
from Core.Entities.Elementos.Abstractos.Informacion.sonido import Sonido, SonidoBase
from Core.Entities.Elementos.Abstractos.Marcadores.Espaciales.agujero import Agujero
from Core.Entities.Elementos.Abstractos.Marcadores.Espaciales.marcador_espacial import (
    Marcador_Espacial,
)
from Core.Entities.Elementos.Abstractos.Marcadores.Espaciales.rastro import Rastro
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.ciclo_lunar import (
    Ciclo_Lunar,
)
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.marcador_temporal import (
    Marcador_Temporal,
)
from Core.Entities.Elementos.Abstractos.Marcadores.marcador import Marcador
from Core.Entities.Elementos.Abstractos.Puzzle.premio import Premio
from Core.Entities.Elementos.Abstractos.Puzzle.puzzle import Puzzle
from Core.Entities.Elementos.Abstractos.Recetas.receta import Receta
from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto
from Core.Entities.Elementos.Simples.Agua.agua import Agua
from Core.Entities.Elementos.Simples.Arbol.arbol import Arbol
from Core.Entities.Elementos.Simples.Bot.bot import Bot
from Core.Entities.Elementos.Simples.Cadaver.cadaver import Cadaver
from Core.Entities.Elementos.Simples.Piedra.piedra import Piedra
from Core.Entities.Elementos.Simples.Comida.Carnes.carne import Carne
from Core.Entities.Elementos.Simples.Comida.Carnes.carne_fresca import Carne_Fresca
from Core.Entities.Elementos.Simples.Comida.Carnes.carne_seca import Carne_Seca
from Core.Entities.Elementos.Simples.Comida.Frutas.fruta import Fruta
from Core.Entities.Elementos.Simples.Comida.Ingredientes.harina import Harina
from Core.Entities.Elementos.Simples.Comida.Ingredientes.masa_pan import Masa_Pan
from Core.Entities.Elementos.Simples.Comida.comida import Comida
from Core.Entities.Elementos.Simples.Etereo.etereo import Etereo
from Core.Entities.Elementos.Simples.Etereo.mensaje import Mensaje
from Core.Entities.Elementos.Simples.Recipiente.recipiente import Recipiente

from Core.Entities.Elementos.elemento_test import Elemento_Test
from Core.Entities.Elementos.elemento import Elemento

import logging

if TYPE_CHECKING:
    from Core.Entities.Mundo.mundo import Mundo

logger = logging.getLogger(__name__)


ELEMENTOS: dict[str, type] = {
    # A
    "Accion": Accion,
    "Agujero": Agujero,
    "Agua": Agua,
    "Arbol": Arbol,
    # B
    "Bot": Bot,
    # C
    "Cadaver": Cadaver,
    "Carne": Carne,
    "Carne_Fresca": Carne_Fresca,
    "Carne_Seca": Carne_Seca,
    "Ciclo_Anual": Ciclo_Anual,
    "Ciclo_Lunar": Ciclo_Lunar,
    "Ciclo_Solar": Ciclo_Solar,
    "Comida": Comida,
    "Condicion": Condicion,
    "CondicionAnd": CondicionAnd,
    "CondicionOr": CondicionOr,
    "CondicionTemperatura": CondicionTemperatura,
    "CondicionTickObjetivo": CondicionTickObjetivo,
    "CondicionUmbralHumedad": CondicionUmbralHumedad,
    "CondicionVecinoCercano": CondicionVecinoCercano,
    # D
    # E
    "Elemento_Abstracto": Elemento_Abstracto,
    "Elemento_Simple": Elemento_Simple,
    "Elemento_Test": Elemento_Test,
    "Estacion": Estacion,
    "Estaciones": Estaciones,
    "Etereo": Etereo,
    # F
    "Fruta": Fruta,
    # G
    # H
    "Harina": Harina,
    "Humedad_Absoluta": Humedad_Absoluta,
    "Humedad_Relativa": Humedad_Relativa,
    # I
    "Informacion": Informacion,
    "Invierno": Estaciones.Invierno,
    # J
    # K
    # L
    # M
    "Marcador": Marcador,
    "Marcador_Espacial": Marcador_Espacial,
    "Marcador_Temporal": Marcador_Temporal,
    "Masa_Pan": Masa_Pan,
    "Mensaje": Mensaje,
    "Mezclar": Mezclar,
    # N
    # O
    "Otono": Estaciones.Otono,
    # P
    "Piedra": Piedra,
    "Premio": Premio,
    "Presion": Presion,
    "Primavera": Estaciones.Primavera,
    "Puzzle": Puzzle,
    # Q
    # R
    "Rastro": Rastro,
    "Raycast": Raycast,
    "Receta": Receta,
    "Recipiente": Recipiente,
    "Reloj": Reloj,
    # S
    "Sistema_Atmosferico": Sistema_Atmosferico,
    "Sonido": Sonido,
    "SonidoBase": SonidoBase,
    "Suelo": Suelo,
    "Suelo_Arena": Suelo_Arena,
    "Suelo_Barro": Suelo_Barro,
    "Suelo_Cesped": Suelo_Cesped,
    "Suelo_Grava": Suelo_Grava,
    "Suelo_Hielo": Suelo_Hielo,
    "Suelo_Oceano": Suelo_Oceano,
    "Suelo_Piedra": Suelo_Piedra,
    "Suelo_Tierra": Suelo_Tierra,
    # T
    "TemperaturaAtmosferica": TemperaturaAtmosferica,
    # U
    # V
    "Verano": Estaciones.Verano,
    "Viento": Viento,
    # W
    # X
    # Y
    # Z
}


def reconstruir_elemento(data: dict, mundo: "Mundo | None" = None):
    nombre_clase = data.get("__clase__")
    clase = ELEMENTOS.get(nombre_clase)
    if clase is None:
        raise ValueError(f"Clase de elemento desconocida: '{nombre_clase}'")

    obj = clase.__new__(clase)

    guardados = set(data.get("comportamientos", {}).keys())
    actuales = {c.__name__ for c in obj._get_comportamientos()}

    for nombre in actuales - guardados:
        comportamiento = COMPORTAMIENTOS.get(nombre)
        if comportamiento is None:
            raise ValueError(f"Comportamiento desconocido: '{nombre}'")
        # Puede haber desaparecido ya en cascada al quitar otro
        # comportamiento del que dependía (ver Comportamiento._sin_comportamiento)
        if isinstance(obj, comportamiento):
            Comportamiento.quitar(obj, comportamiento)

    for nombre in guardados - actuales:
        comportamiento = COMPORTAMIENTOS.get(nombre)
        if comportamiento is None:
            raise ValueError(f"Comportamiento desconocido: '{nombre}'")
        valores = data["comportamientos"].get(nombre, {})
        # Puede haber aparecido ya en cascada al añadir otro que lo trae
        # consigo por herencia (p.ej. añadir Peso ya trae Fisico)
        if not isinstance(obj, comportamiento):
            Comportamiento.anhadir(obj, comportamiento, **valores)

    obj.deserializar(data, mundo)
    return obj


def construir_elemento(nombre_clase: str, **campos):
    """
    Construye un elemento NUEVO llamando a su __init__ real -- se
    ejecutan sus validaciones (ej. Peso_Zero en Piedra) y efectos
    secundarios propios del constructor (ej. la generación de sonido
    de Piedra), justo lo que reconstruir_elemento() NO hace a
    propósito (ver su docstring: usa __new__ + deserializar() porque
    restaura un elemento que ya pasó por __init__ en algún momento
    anterior de su vida, no vuelve a repetirlo).

    Se usa cuando la creación es "mágica": alguien decide, ahora
    mismo, que este elemento empieza a existir con estos datos (una
    acción del mundo, un comando de consola...) -- no cuando se está
    restaurando algo que ya existía.
    """
    clase = ELEMENTOS.get(nombre_clase)
    if clase is None:
        raise ValueError(f"Clase de elemento desconocida: '{nombre_clase}'")
    return clase(**campos)


def _todas_las_subclases(cls: type) -> set[type]:
    directas = set(cls.__subclasses__())
    return directas | {
        nieta for hija in directas for nieta in _todas_las_subclases(hija)
    }


def _avisar_si_falta_registrar():

    reales = set(_todas_las_subclases(Elemento))
    registradas = set(ELEMENTOS.values())
    faltantes = reales - registradas
    if faltantes:
        nombres = ", ".join(sorted(c.__name__ for c in faltantes))
        logger.warning(
            "ELEMENTOS: hay clase(s) Elemento definidas pero sin registrar "
            "(no se podrán reconstruir desde snapshot/red hasta que se "
            "añadan): %s",
            nombres,
        )


_avisar_si_falta_registrar()
