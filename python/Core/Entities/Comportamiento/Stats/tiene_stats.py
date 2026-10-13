# Core/Entities/Comportamiento/Stats/tiene_stats.py

from Core.Entities.Comportamiento.Stats.stat_derivado import Stat_Derivado
from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Entities.Comportamiento.Stats.stat import Stat


class Tiene_Stats(Comportamiento):
    """
    Comportamiento (mixin) que da a un Elemento la capacidad de "tener
    stats". Recibe una lista de instancias de Stat ya construidas: quien
    crea el Elemento (p.ej. Bot.__init__) decide qué stats tiene y con qué
    valor inicial, en vez de que Tiene_Stats los invente.

    Parametros:

    - stats: list[Stat] = None
    """

    def __init__(self, stats: list[Stat] = None, **kwargs):
        super().__init__(**kwargs)
        self._stats: dict[str, Stat] = {}
        for stat in stats or []:
            if stat.nombre in self._stats:
                # Dos stats con el mismo nombre es un error de quien
                # construye el Elemento: se avisa, no se sobreescribe.
                raise ValueError(f"Stat duplicado: '{stat.nombre}'")
            self._stats[stat.nombre] = stat

    # --- Acceso ---

    def get_stat(self, nombre: str):
        """Valor actual de un stat. KeyError explícito si no existe."""
        return self._stats[nombre].valor

    def set_stat(self, nombre: str, valor) -> None:
        self._stats[nombre].valor = valor

    def tiene_stat(self, nombre: str) -> bool:
        return nombre in self._stats

    def listar_stats(self) -> dict:
        return dict(self._stats)

    def recalcular_derivados(self) -> None:
        """
        Recalcula todos los Stat_Derivado EN EL ORDEN en que se pasaron a
        __init__. Ese orden importa: si un derivado depende de otro
        derivado, quien construye la lista debe colocar el dependido antes.
        """
        for stat in self._stats.values():
            if isinstance(stat, Stat_Derivado):
                stat.recalcular()

    # --- Hooks por campo (conversión de formato) ---
    # También los usa Elemento.aplicar_patch (clave "stats" del patch).

    def serializar_stats(self) -> dict:
        """Estado ACTUAL de cada stat ({nombre: valor}), no la lista de
        instancias que se recibió en __init__."""
        return {nombre: stat.valor for nombre, stat in self._stats.items()}

    def deserializar_stats(self, value: dict) -> None:
        """
        Inverso de serializar_stats().

        reconstruir_elemento() crea el objeto con __new__ (sin __init__),
        así que aquí es donde se crea self._stats para un elemento que
        llega por red o snapshot.

        - Si el stat YA existe se actualiza su valor (conserva su clase,
          p.ej. Stat_Derivado): así un patch parcial de consola no destruye
          los stats derivados.
        - Si no existe se crea como Stat "plano" (solo se dispone de
          nombre/valor, no de los parámetros de construcción de la
          subclase).

        LIMITACIÓN CONOCIDA: tras un roundtrip los stats son planos, por lo
        que recalcular_derivados() no hace nada y se pierden atributos
        extra de un stat (p.ej. Edad.edad_adulta).
        """
        if getattr(self, "_stats", None) is None:
            self._stats = {}
        for nombre, valor in value.items():
            if nombre in self._stats:
                self._stats[nombre].valor = valor
            else:
                self._stats[nombre] = Stat(nombre=nombre, valor=valor)

    # --- Cadena serializar / representar / deserializar ---
    # Misma firma que en Comportamiento; llaman a super() primero y añaden
    # solo su sección (si no, Elemento.serializar lanza NotImplementedError).

    def serializar(self) -> dict:
        """Snapshot / transporte: los valores de todos los stats."""
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {
            "stats": self.serializar_stats()
        }
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Unity: mismos valores que serializar (ASUNCIÓN: Unity recibe
        todos los stats; si no, filtrar aquí)."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {
                "stats": self.serializar_stats()
            }
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        self.deserializar_stats(data["comportamientos"][__class__.__name__]["stats"])
