# Core/Entities/Comportamiento/Material/transformable.py
from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Comportamiento.Material.registro_transformaciones import (
    REGISTRO_TRANSFORMACIONES,
)
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion
from Core.Entities.entity import Modos


class Transformable(Material):
    """
    dict_transformable: dict[Condicion, str] -- el string es el nombre
    de la transformación en REGISTRO_TRANSFORMACIONES, NUNCA un
    Callable directo: así el diccionario entero es serializable (la
    llave porque Condicion es un Elemento con campos propios, el valor
    porque es un string plano) y sobrevive a cualquier reserialización
    a mitad de una transformación en curso (p.ej. a media franja de
    espera, ver CondicionTickObjetivo).
    """

    REQUIERE = {"dict_transformable: dict[str, Condicion]"}
    ABSTRACTOS = {}

    def __init__(self, dict_transformable: dict[Condicion, str], **kwargs):
        super().__init__(**kwargs)
        self.dict_transformable = dict_transformable

    def get_condiciones(self) -> list[Condicion]:
        return list(self.dict_transformable.keys())

    def tick(self, pos: tuple[int, int], ctx) -> None:
        """Una transformación por tick -- si en algún caso real hiciera
        falta encadenar varias en el mismo tick, esto habría que
        revisarlo entonces. Se itera sobre una copia (list(...)) porque
        el propio callable puede mutar dict_transformable (caso franja:
        al cumplirse la condición de entrada, se sustituyen las
        condiciones vigentes por las de cuenta/salida)."""
        for condicion, nombre_transformacion in list(self.dict_transformable.items()):
            if condicion.modo is not Condicion.Modo.LOCAL:
                continue
            if condicion.evaluar(self, ctx):
                funcion = REGISTRO_TRANSFORMACIONES.get(nombre_transformacion)
                if funcion is None:
                    raise ValueError(
                        f"Transformación desconocida: '{nombre_transformacion}'"
                    )
                funcion(self, ctx)
                return

    def serialize_dict_transformable(self) -> list[dict]:
        """
        Se serializa siempre con modo=Modos.guardado, independientemente
        del modo real de esta llamada -- una Condicion necesita
        fidelidad completa para ser reconstruible pase lo que pase
        (mismo razonamiento que 'transporte' == 'guardado' en
        Comportamiento.serializar): no tiene sentido una versión
        "ligera" de una condición, a diferencia de otros campos que sí
        se aligeran para 'representacion'.
        """
        return [
            {
                "transformacion": nombre,
                "condicion": condicion.serializar(modo=Modos.guardado),
            }
            for nombre, condicion, in self.dict_transformable.items()
        ]

    def deserialize_dict_transformable(self, valor: list[dict]) -> None:
        # Import diferido: evita ciclo Transformable -> registry -> ... -> Transformable
        from Core.Entities.Elementos.registry import reconstruir_elemento

        self.dict_transformable = {
            reconstruir_elemento(entrada["condicion"], self.mundo): entrada[
                "transformacion"
            ]
            for entrada in valor
        }

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return ["dict_transformable"]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
- El Elemento puede transformarse en otro (ser eliminado y crear otro nuevo)
o cambiar sus comportamientos, al cumplirse ciertas condiciones LOCAL.

Atributos:
\tdict_transformable: dict[Condicion, str]  (nombre en REGISTRO_TRANSFORMACIONES)

Métodos:
\tget_condiciones(self) -> list[Condicion]
        """
