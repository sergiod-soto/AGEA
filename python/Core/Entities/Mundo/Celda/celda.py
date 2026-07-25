# Core/Entities/Elementos/Simples/Celda/celda.py
from typing import Optional
from numpy import uint64

from Core.Entities.Elementos.Abstractos.Bioma.Suelo.suelo import Suelo
from Core.Entities.Elementos.elemento import Elemento


class Celda:
    suelo: Suelo
    bot: uint64 | None
    contenido: list[uint64]
    inocupable: bool

    def __init__(self, suelo) -> None:
        self.suelo = suelo
        self.inocupable = False

    def put_elemento(self, elemento: Elemento) -> bool:
        if elemento.excluyente_en_celda:
            if self.inocupable:
                return False
            else:
                self.inocupable = True
        self.contenido.append(elemento.id)
        return True

    def remove_elemento(self, elemento: Elemento) -> bool:
        # busco
        elemento_guardado = None
        for id_contenido in self.contenido:
            if id_contenido == elemento.id:
                elemento_guardado = elemento
                break

        if elemento_guardado == None:
            return False

        # era o no excluyente
        if elemento_guardado.excluyente_en_celda:
            self.inocupable = False
        self.contenido.remove(elemento.id)
        return True
