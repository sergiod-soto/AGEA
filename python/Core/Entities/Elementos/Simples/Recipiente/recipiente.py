from Core.Entities.Elementos.Simples.elemento_simple import Elemento_Simple


# TODO: terminar de definir Recipiente
class Recipiente(Elemento_Simple):
    def __init__(
        self,
        tipo,
        tamanho,
        casilla,
        capa,
        rotacion=0,
        persistente_en_memoria=False,
        fuerza_cargado_chunks=False,
    ):
        super().__init__(
            tipo,
            tamanho,
            casilla,
            capa,
            rotacion,
            persistente_en_memoria,
            fuerza_cargado_chunks,
        )
        # TODO: terminar de definir Recipiente
