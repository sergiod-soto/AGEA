# Core/Entities/Elementos/Abstractos/Condiciones/Condiciones_Fisicas/condicion_vecino_cercano.py


import json

from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class CondicionVecinoCercano(Condicion):
    """
    True si, dentro de 'radio' casillas (distancia Chebyshev, ver
    TickContext.celdas_en_radio) de la posición de 'propietario', existe
    al menos un elemento cuyo tipo se llame 'tipo_buscado'.

    'tipo_buscado' se guarda como STRING (nombre de clase), no como la
    clase en sí -- una clase Python no es serializable de forma trivial
    con el mecanismo genérico de Elemento (a diferencia de un string,
    que Elemento.serializar() ya vuelca tal cual sin necesitar ningún
    hook). La comparación se hace por type(elemento).__name__.

    Busca únicamente en el slot 'suelo' de cada celda (celda.suelo) --
    tiene sentido para el caso de uso actual (Suelo_Cesped es siempre
    de terreno), pero si en el futuro hiciera falta buscar tipos que
    vivan en 'bot' o 'resto', este método tendría que extenderse para
    recorrer también esos slots.

    'propietario' debe exponer 'casilla' -- lo cumple Suelo.
    """

    CAMPOS = ("tipo_buscado", "radio")

    def __init__(self, tipo_buscado: str, radio: int, **kwargs):
        super().__init__(**kwargs)
        self.tipo_buscado = tipo_buscado
        self.radio = radio

    def evaluar(self, propietario, ctx) -> bool:
        x, y = propietario.casilla
        for celda in ctx.celdas_en_radio(x, y, self.radio):
            suelo = celda.suelo
            if not suelo:
                continue
            if isinstance(suelo, (bytes, bytearray)):
                # Celda de la ghost zone (proto): el suelo va serializado. Solo
                # se lee el nombre de clase; coste asumible porque afecta solo a
                # las celdas del margen de un Sector.
                nombre = json.loads(suelo.decode())["__clase__"]
            else:
                nombre = type(suelo).__name__
            if nombre == self.tipo_buscado:
                return True
        return False

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "tipo_buscado",
            "radio",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return (
            "Se cumple si hay un elemento del tipo indicado en el slot "
            "'suelo' dentro de un radio de casillas alrededor del propietario."
        )
