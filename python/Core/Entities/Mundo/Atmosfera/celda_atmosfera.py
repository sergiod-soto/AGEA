# Core/Entities/Mundo/Celda/celda_atmosfera.py

from vectors import Vector2

from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.temperatura import (
    Temperatura,
)
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.presion import (
    Presion,
)
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.viento import (
    Viento,
)
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.humedad_absoluta import (
    Humedad_Absoluta,
)
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Derivado.humedad_relativa import (
    Humedad_Relativa,
)


class Celda_Atmosfera:

    def __init__(
        self,
        posicion: tuple[int, int],
        resistencia_viento: float,
        direccion_preferente_viento: Vector2,
        fuerza_viento: Vector2,
    ) -> None:
        self.posicion = posicion

        # Radiación: no tiene clase Sistema_Atmosferico propia (se
        # calcula cada tick en
        # Infraestructura/Gestores/Mundo/Atmosfera/sistema_atmosferico.py
        # a partir del ciclo solar y, a futuro, nubes/árboles) -- se
        # guarda aquí como float simple, igual que antes.
        self.radiacion: float = 0.0

        # Magnitudes primarias/derivadas: cada una es ahora su propio
        # Sistema_Atmosferico, con su propio estado (.valor, o
        # .intensidad/.direccion en el caso de Viento) y su propio
        # actualizar(). El orquestador
        # (Infraestructura/Gestores/Mundo/Atmosfera/sistema_atmosferico.py)
        # las llama en orden cada tick: temperatura -> presion -> viento
        # -> humedad_absoluta -> humedad_relativa.
        self.temperatura = Temperatura(valor_inicial=20.0)
        self.presion = Presion(valor_inicial=1000.0)
        self.viento = Viento()
        self.humedad_absoluta = Humedad_Absoluta(valor_inicial=0.0)
        self.humedad_relativa = Humedad_Relativa(valor_inicial=0.0)

        # propiedades relacionadas con el terreno (sin cambios):
        self.resistencia_viento = resistencia_viento  # 0 = libre, 1 = bloqueado
        self.direccion_preferente_viento = direccion_preferente_viento
        self.fuerza_viento = fuerza_viento

    def aplicar_patch(self, patch: dict) -> None:
        """
        ATENCIÓN -- este método quedó a medias tras el cambio de
        arquitectura y hay que decidir qué hacer con él antes de que
        alguien lo use para sincronizar atmósfera por red:

        Sigue haciendo setattr(self, nombre, valor) plano, que es
        correcto para resistencia_viento, direccion_preferente_viento y
        fuerza_viento. Pero
        temperatura/presion/viento/humedad_absoluta/humedad_relativa ya
        NO son floats/Vector2 sueltos, sino objetos Sistema_Atmosferico
        con su propio estado -- un patch tipo {"temperatura": 25.0}
        SUSTITUIRÍA el objeto Temperatura entero por un float 25.0,
        rompiendo cualquier código posterior que llame a
        celda.temperatura.actualizar(...).

        Pendiente de decidir dónde se arregla: aquí (p.ej. detectando si
        el atributo actual es un Sistema_Atmosferico y, en ese caso,
        asignando a su .valor en vez de reemplazarlo), o en quien genera
        esos patches (Logica_Mundo.actualizar_atmosfera).
        """
        for nombre, valor in patch.items():
            setattr(self, nombre, valor)

