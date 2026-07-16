# Core/Entities/Elementos/Simples/Agua/recetas_con.py
from Core.Entities.Elementos.Abstractos.Recetas.receta import Receta


def recetas_con_agua() -> dict[str, Receta]:
    from Core.Entities.Elementos.Abstractos.Recetas.lista_recetas import (
        Lista_Recetas,
    )

    return {
        "MASA_PAN": Lista_Recetas.Mezclar.Comida.MASA_PAN,
    }
