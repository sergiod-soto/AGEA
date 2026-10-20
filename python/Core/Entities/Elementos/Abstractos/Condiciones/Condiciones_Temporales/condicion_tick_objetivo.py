# Core/Entities/Elementos/Abstractos/Condiciones/Condiciones_Temporales/condicion_tick_objetivo.py


from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class CondicionTickObjetivo(Condicion):
    """
    True cuando ctx.tick_id alcanza tick_objetivo. tick_objetivo es un
    campo plano fijado UNA vez al crear la condición (al entrar en la
    franja).
    """

    CAMPOS = ("tick_objetivo",)

    def __init__(self, tick_objetivo: int, **kwargs):
        super().__init__(**kwargs)
        self.tick_objetivo = tick_objetivo

    def evaluar(self, propietario, ctx) -> bool:
        return ctx.tick_id >= self.tick_objetivo

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return ["tick_objetivo"]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return "Se cumple cuando el tick actual alcanza un tick objetivo fijado de antemano."
