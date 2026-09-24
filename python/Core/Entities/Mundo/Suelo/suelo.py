# Core/Entities/Elementos/Abstractos/Bioma/Suelo/suelo.py
"""
Suelo — elemento que ocupa el slot 'suelo' de cada Celda del mundo.

Representa el terreno de una casilla concreta. Por sí solo no declara
ningún comportamiento (la clase está vacía a propósito): los biomas o
tipos de terreno concretos se añaden dinámicamente vía
Comportamiento.anhadir(suelo_instancia, Piedra, ...), igual que se
haría con cualquier otro Elemento — Suelo solo aporta la identidad
("esta casilla tiene terreno") y su posición.

No hereda de Elemento_Simple: 'tamanho' y 'rotacion' no tienen sentido
para una casilla de terreno (una casilla no "rota" ni tiene un tamaño
distinto de 1x1 por definición). Por eso Suelo añade 'casilla' él
mismo, igual que hace Elemento_Simple, pero sin arrastrar los otros
dos campos que no le sirven de nada.
"""

from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto


class Suelo(Elemento_Abstracto):

    def __init__(
        self,
        casilla: tuple[int, int],
        id_elemento,
        tipo,
        tasa_conversion_radiacion_calor,
        inercia_termica,
        **kwargs,
    ):
        super().__init__(
            tipo=tipo,
            id_elemento=id_elemento,
            **kwargs,
        )
        self.casilla = casilla
        self.tasa_conversion_radiacion_calor = tasa_conversion_radiacion_calor
        self.inercia_termica = inercia_termica

    def serializar_casilla(self) -> dict:
        """
        Mismo formato {"x":, "y":} que ya usan otros elementos en su
        'representacion()' (ver Elemento_Test.representacion, que llama
        a self.serializar_casilla() con esta misma forma) — Unity espera
        esta estructura para 'casilla' en cualquier tipo de elemento,
        no solo en Suelo.
        """
        x, y = self.casilla
        return {"x": x, "y": y}

    def representacion(self, modo: str, incluir: list[str] = None) -> dict:
        """
        A diferencia del resto de elementos, 'comportamientos' aquí NO se
        filtra por incluir — el suelo siempre manda todos sus
        comportamientos completos (decisión explícita: el suelo es la
        base visual imprescindible, no un dato opcional como el resto).
        """
        campos = {
            "elemento": {
                "casilla": self.serializar_casilla(),
                **self.serializar_elemento(),
            },
            "comportamientos": {
                cls.__name__: self.serializar(cls, modo=modo)
                for cls in self._get_comportamientos()
            },
        }
        return campos
