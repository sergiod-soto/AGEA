# Core/Entities/Comportamiento/Material/transformable.py
from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Comportamiento.Material.registro_transformaciones import (
    REGISTRO_TRANSFORMACIONES,
)
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


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

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"transformable": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"transformable": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    def get_condiciones(self) -> list[Condicion]:
        return list(self.dict_transformable.keys())

    def tick_comportamiento(self, pos: tuple[int, int], ctx) -> None:
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

    def serializar_dict_transformable(self) -> list[dict]:
        return [
            {
                "transformacion": nombre,
                "condicion": condicion.serializar(),
            }
            for nombre, condicion, in self.dict_transformable.items()
        ]

    def deserializar_dict_transformable(self, valor: list[dict]) -> None:
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
