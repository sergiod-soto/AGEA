# Core/Entities/Elementos/Simples/Piedra/piedra.py

from Core.Entities.Comportamiento.Energetico.termico import Termico
from Core.Entities.Comportamiento.Fisico.empujable import Empujable
from Core.Entities.Comportamiento.Fisico.enterrable import Enterrable
from Core.Entities.Comportamiento.Fisico.peso import Peso
from Core.Entities.Comportamiento.Fisico.volumen import Volumen
from Core.Entities.Comportamiento.Informativo.color import Color
from Core.Entities.Comportamiento.Informativo.sonoro import Sonoro
from Core.Entities.Comportamiento.Interaccion.agarrable import Agarrable
from Core.Entities.Comportamiento.Interaccion.crafteable import Crafteable
from Core.Entities.Comportamiento.Interaccion.destruible import Destruible
from Core.Entities.Comportamiento.Interaccion.golpeable import Golpeable
from Core.Entities.Comportamiento.Interaccion.ingrediente import Ingrediente
from Core.Entities.Comportamiento.Material.erosionable import Erosionable
from Core.Entities.Comportamiento.Material.solido import Solido
from Core.Entities.Comportamiento.Material.tangible import Tangible
from Core.Entities.Comportamiento.Social.intercambiable import Intercambiable
from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Entities.Elementos.Abstractos.Acciones.accion import Accion
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion
from Core.Entities.Elementos.Abstractos.Informacion.sonido import SonidoBase
from Core.Entities.Elementos.Simples.elemento_simple import Elemento_Simple
from Core.Entities.Elementos.elemento import Elemento
from Exceptions.Bot.comportamientos_exceptions import Peso_Zero

comportamientos = Comportamiento.declarar_comportamientos(
    Agarrable,
    Color,
    Destruible,
    Empujable,
    Enterrable,
    Erosionable,
    Golpeable,
    Ingrediente,
    Intercambiable,
    Peso,
    Solido,
    Sonoro,
    Tangible,
    Termico,
    Volumen,
)


class Piedra(Elemento_Simple, comportamientos):

    # serializar / representar / deserializar: NO se definen aquí. Piedra no
    # tiene datos propios; la cadena super() cubre Elemento, Elemento_Simple
    # y cada comportamiento de arriba (cada uno escribe su sección).

    def __init__(
        self,
        id_elemento: int,
        tamanho: int,
        casilla: tuple[int, int],
        capa: int,
        #
        # Peso:
        peso: float,
        # Empujable:
        coste_empujar: float,
        # Volumen:
        volumen: float,
        # Color:
        rgb_base: tuple[int, int, int],
        # Termico:
        temperatura_propia: float,
        tasa_transferencia_temperatura: float,
        # Agarrable:
        agarrado_por: Elemento = None,
        # Destruible:
        durabilidad_max_destruible: float = None,
        # Erosionable:
        durabilidad_max_erosion=1,
        condiciones_erosion: list[tuple[list[Condicion], float]] = None,
        #
        **kwargs
    ):
        # comprobaciones:
        if peso == 0:
            raise Peso_Zero()

        # _______________________________________
        #   creacion de libreria de sonidos
        # _______________________________________
        #

        # sonido golpear 1

        # base1
        duracion = 0.13
        fundamental = 3654.63 / (peso ** (1 / 3))  # Hz — más masa → más grave
        amplitudes = [0.9998, 0.1629, 0.1576, 0.0205, 0.0441]

        base1 = SonidoBase.generar_frecuencia(
            duracion,
            fundamental,
            amplitudes,
        )

        # base2
        duracion = 0.13
        fundamental = 3106.64 / (peso ** (1 / 3))  # Hz — más masa → más grave
        amplitudes = [0.9999, 0.2466, 0.1005, 0.2396, 0.0207, 0.0090]

        base2 = SonidoBase.generar_frecuencia(
            duracion,
            fundamental,
            amplitudes,
        )

        sonido_golpear_1 = SonidoBase.fusionar(base1, base2)
        sonido_golpear_1.guardar_en_biblioteca()

        super().__init__(
            tipo=Piedra,
            id_elemento=id_elemento,
            tamanho=tamanho,
            casilla=casilla,
            capa=capa,
            # Peso:
            peso=peso,
            # Enterrable:
            coste_empujar=coste_empujar,
            # Volumen:
            volumen=volumen,
            # Color:
            rgb_base=rgb_base,
            # Agarrable:
            agarrado_por=agarrado_por,
            # Ingrediente:
            recetas_de=None,
            # Termico:
            temperatura_propia=temperatura_propia,
            tasa_transferencia_temperatura=tasa_transferencia_temperatura,
            # Destruible:
            durabilidad_max_destruible=durabilidad_max_destruible,
            # Erosionable:
            durabilidad_max_erosion=durabilidad_max_erosion,
            condiciones_erosion=condiciones_erosion,
            # Sonoro:
            sonidos={
                "GOLPEAR": [sonido_golpear_1],
                "EMPUJAR": [],
            },
            **kwargs,
        )

    def soltar(self, por: Elemento): ...
    def agarrar(self, por: Elemento): ...
    def erosionar(self, cantidad: float): ...
    def danhar(self, danho: float): ...
    def check_push(self, direccion) -> Elemento | bool: ...
    def golpear(self, por: Elemento): ...
    def check_desenterrable(self) -> bool: ...
    def check_enterrable(self) -> bool: ...
    def _destruir(self, efecto: Accion): ...
    def enterrar(self) -> bool: ...
    def desenterrar(self) -> bool: ...
    def push(self, direccion) -> bool: ...
    def restaurar(self, danho: float): ...
    def _destruir(self, danho: float): ...

    def tick_elemento(self, ctx): ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        # Todos los parámetros obligatorios de __init__, en el mismo
        # orden que aparecen ahí (facilita comparar visualmente si
        # cambia la firma del constructor).
        return [
            *["tamanho", "casilla", "capa"],
            *Peso.campos_para_creacion(),
            *Empujable.campos_para_creacion(),
            *Volumen.campos_para_creacion(),
            *Color.campos_para_creacion(),
            *Termico.campos_para_creacion(),
            *Agarrable.campos_para_creacion(),
            *Destruible.campos_para_creacion(),
            *Erosionable.campos_para_creacion(),
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return (
            "Una piedra\n"
            "\n"
            "Atributos:\n"
            "\ttamanho: int\n"
            "\tcasilla: tuple[int, int]\n"
            "\tcapa: int\n"
            "\tpeso: float\n"
            "\tcoste_empujar: float\n"
            "\tvolumen: float\n"
            "\trgb_base: tuple[int, int, int]\n"
            "\ttemperatura_propia: float\n"
            "\ttasa_transferencia_temperatura: float\n"
            "\tagarrado_por: Elemento = None\n"
            "\tdurabilidad_max_destruible: float = None\n"
            "\tdurabilidad_max_erosion=1 (a cambiar)\n"
        )
