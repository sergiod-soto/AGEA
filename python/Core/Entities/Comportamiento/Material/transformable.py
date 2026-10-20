# Core/Entities/Comportamiento/Material/transformable.py


from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Comportamiento.Material.registro_transformaciones import (
    REGISTRO_TRANSFORMACIONES,
)
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class Transformable(Material):
    """
    dict_transformable: dict[str, Condicion]. La CLAVE es el nombre de la
    transformación en REGISTRO_TRANSFORMACIONES (nunca un Callable) y el valor
    su Condicion. El nombre es único por elemento (una transformación, una
    condición; para varias, CondicionAnd/Or) y hace de id estable de la
    condición: (id_elemento del dueño, nombre). Así el dict entero es
    serializable y sobrevive a una reserialización a mitad de una cuenta.
    """

    REQUIERE = {"dict_transformable: dict[str, Condicion]"}
    ABSTRACTOS = {}

    def __init__(self, dict_transformable: dict[str, Condicion], **kwargs):
        super().__init__(**kwargs)
        self.dict_transformable = dict_transformable

    def serializar(self) -> dict:
        datos = super().serializar()
        # La guarda de Elemento.serializar exige que la sección incluya TODOS
        # los campos del __init__ (aquí, dict_transformable).
        datos["comportamientos"][__class__.__name__] = {
            "dict_transformable": self.serializar_dict_transformable()
        }
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"transformable": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        seccion = data["comportamientos"][__class__.__name__]
        # 'mundo' se pasa a mano: Elemento.deserializar asigna self.mundo
        # DESPUÉS de esta cadena y el objeto viene de __new__.
        self.deserializar_dict_transformable(seccion["dict_transformable"], mundo)

    def get_condiciones(self) -> list[Condicion]:
        return list(self.dict_transformable.values())

    def tick_comportamiento(self, ctx) -> None:
        """Una transformación por tick -- si en algún caso real hiciera
        falta encadenar varias en el mismo tick, esto habría que
        revisarlo entonces. Se itera sobre una copia (list(...)) porque
        el propio callable puede mutar dict_transformable (caso franja:
        al cumplirse la condición de entrada, se sustituyen las
        condiciones vigentes por las de cuenta/salida)."""
        for nombre_transformacion, condicion in list(self.dict_transformable.items()):
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
            {"transformacion": nombre, "condicion": condicion.serializar()}
            for nombre, condicion in self.dict_transformable.items()
        ]

    def deserializar_dict_transformable(self, valor: list[dict], mundo=None) -> None:
        # Import diferido: evita ciclo Transformable -> registry -> ... -> Transformable
        from Core.Entities.Elementos.registry import reconstruir_elemento

        # aplicar_patch lo llama con un solo argumento: ahí self.mundo ya existe.
        mundo = mundo if mundo is not None else getattr(self, "mundo", None)
        self.dict_transformable = {
            entrada["transformacion"]: reconstruir_elemento(entrada["condicion"], mundo)
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
\tdict_transformable: dict[str, Condicion]  (nombre en REGISTRO_TRANSFORMACIONES)

Métodos:
\tget_condiciones(self) -> list[Condicion]
        """
