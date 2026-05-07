from Core.Entities.Comportamiento.Fisico.peso import Peso
from Core.Entities.Comportamiento.Fisico.volumen import Volumen
from Core.Entities.Comportamiento.Informativo.color import Color
from Core.Entities.Comportamiento.Interaccion.consumible import Consumible
from Core.Entities.Comportamiento.Interaccion.crafteable import Crafteable
from Core.Entities.Comportamiento.Interaccion.ingrediente import Ingrediente
from Core.Entities.Comportamiento.Material.combinable import Combinable

from Core.Entities.Comportamiento.Material.divisible import Divisible
from Core.Entities.Comportamiento.Material.gaseoso import Gaseoso
from Core.Entities.Comportamiento.Material.liquido import Liquido
from Core.Entities.Comportamiento.Material.solido import Solido
from Core.Entities.Comportamiento.Material.tangible import Tangible
from Core.Entities.Comportamiento.Material.transformable import Transformable
from Core.Entities.Comportamiento.Material.transparente import Transparente
from Core.Entities.Comportamiento.Salud.comestible import Comestible
from Core.Entities.Comportamiento.Salud.hidratante import Hidratante
from Core.Entities.Comportamiento.Salud.medicinal import Medicinal
from Core.Entities.Comportamiento.Salud.nutritivo import Nutritivo
from Core.Entities.Comportamiento.Salud.toxico import Toxico
from Core.Entities.Comportamiento.Temporal.perecedero import Perecedero
from Core.Entities.Elementos.Simples.elemento_simple import Elemento_Simple
from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Entities.Elementos.elemento import Elemento

comportamientos = Comportamiento.declarar_comportamientos(
    Peso,
    Consumible,
    Volumen,
    Ingrediente,
    Combinable,
    Divisible,
    Solido,
    Liquido,
    Gaseoso,
    Tangible,
    Transformable,
    Transparente,
    Comestible,
    Hidratante,
    Color,
    Medicinal,
    Toxico,
    Nutritivo,
    Perecedero,
)


class Agua(Elemento_Simple, comportamientos):

    cantidad_max = 20

    def __init__(
        self,
        casilla: tuple[int, int],
        cantidad: int,
        masa: float,
        volumen: float,
        rgb_color: tuple[int, int, int],
        recetas: dict[str, Crafteable],
        elemento_combinable: Elemento,
        cantidad_max_combinable: float = None,
    ):
        super().__init__(tipo=Agua, tamanho=1, casilla=casilla, capa=1)
        self.cantidad = cantidad
