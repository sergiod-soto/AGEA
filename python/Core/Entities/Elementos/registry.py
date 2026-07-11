# Core/Entities/Elementos/registry.py
"""
registry_elementos.py — Mapa nombre de clase → clase, para reconstruir
elementos serializados (ver Elemento.serializar/deserializar).

Para añadir un elemento nuevo: importarlo aquí y añadirlo a ELEMENTOS.
"""

from Core.Entities.Comportamiento.Interaccion.ingrediente import Ingrediente
from Core.Entities.Comportamiento.Stats.Informacion.informacion import Informacion
from Core.Entities.Comportamiento.Terreno.piedra import Piedra
from Core.Entities.Elementos.Abstractos.Acciones.accion import Accion
from Core.Entities.Elementos.Abstractos.Acciones.mezclar import Mezclar
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion
from Core.Entities.Elementos.Abstractos.Informacion.raycast import Raycast
from Core.Entities.Elementos.Abstractos.Informacion.sonido import Sonido
from Core.Entities.Elementos.Abstractos.Marcadores.Espaciales.agujero import Agujero
from Core.Entities.Elementos.Abstractos.Marcadores.Espaciales.marcador_espacial import (
    Marcador_Espacial,
)
from Core.Entities.Elementos.Abstractos.Marcadores.Espaciales.rastro import Rastro
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.ciclo_lunar import (
    Ciclo_Lunar,
)
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.clima import Clima
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.marcador_temporal import (
    Marcador_Temporal,
)
from Core.Entities.Elementos.Abstractos.Marcadores.marcador import Marcador
from Core.Entities.Elementos.Abstractos.Puzzle.premio import Premio
from Core.Entities.Elementos.Abstractos.Puzzle.puzzle import Puzzle
from Core.Entities.Elementos.Abstractos.Recetas.receta import Receta
from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto
from Core.Entities.Elementos.Simples.Agua.agua import Agua
from Core.Entities.Elementos.Simples.Arbol import Arbol
from Core.Entities.Elementos.Simples.Bot.Bot import Bot
from Core.Entities.Elementos.Simples.Cadaver.cadaver import Cadaver
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
from Infraestructura.Gestores.Mundo.Logica_Mundo.logica_mundo import Celda

ELEMENTOS: dict[str, type] = {
    "Accion": Accion,
    "Mezclar": Mezclar,
    "Condicion": Condicion,
    "Informacion": Informacion,
    "Raycast": Raycast,
    "Sonido": Sonido,
    "Marcador": Marcador,
    "Marcador_Espacial": Marcador_Espacial,
    "Agujero": Agujero,
    "Rastro": Rastro,
    "Ciclo_Lunar": Ciclo_Lunar,
    "Clima": Clima,
    "Marcador_Temporal": Marcador_Temporal,
    "Puzzle": Puzzle,
    "Premio": Premio,
    "Receta": Receta,
    "Elemento_Abstracto": Elemento_Abstracto,
    "Agua": Agua,
    "Arbol": Arbol,
    "Bot": Bot,
    "Cadaver": Cadaver,
    "Celda": Celda,
    "Comida": Comida,
    "Carne": Carne,
    "Carne_Seca": Carne_Seca,
    "Carne_Fresca": Carne_Fresca,
    "Fruta": Fruta,
    "Ingrediente": Ingrediente,
    "Masa_Pan": Masa_Pan,
    "Harina": Harina,
    "Etereo": Etereo,
    "Mensaje": Mensaje,
    "Piedra": Piedra,
    "Recipiente": Recipiente,
}


def reconstruir_elemento(data: dict):
    """
    Reconstruye una instancia completa a partir de su forma serializada
    (ver Elemento.serializar), sin pasar por __init__ — que exige
    argumentos de creación (padres/tamanho/casilla...) que no aplican
    al restaurar un elemento ya existente.
    """
    nombre_clase = data.get("__clase__")
    clase = ELEMENTOS.get(nombre_clase)
    if clase is None:
        raise ValueError(f"Clase de elemento desconocida: '{nombre_clase}'")

    obj = clase.__new__(clase)
    obj.deserializar(data)
    return obj
