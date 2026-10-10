# Core/Entities/Comportamiento/Stats/tiene_stats.py

from Core.Entities.Comportamiento.Stats.stat_derivado import Stat_Derivado
from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Entities.Comportamiento.Stats.stat import Stat


# Comportamiento (mixin) que da a un Elemento la capacidad de "tener
# stats". Recibe una lista de instancias de Stat ya construidas -- quien
# crea el Elemento (p.ej. Bot.__init__) decide explicitamente que stats
# tiene y con que valor inicial, en vez de que Tiene_Stats los invente.
class Tiene_Stats(Comportamiento):
    """
    Parametros:

    - stats: list[Stat] = None

    Metodos abstractos:

    -
    """

    def __init__(self, stats: list[Stat] = None, **kwargs):
        super().__init__(**kwargs)
        self._stats: dict[str, Stat] = {}
        for stat in stats or []:
            if stat.nombre in self._stats:
                # dos stats con el mismo nombre en la misma lista es un
                # error de quien construye el Elemento, no algo a
                # silenciar sobreescribiendo
                raise ValueError(f"Stat duplicado: '{stat.nombre}'")
            self._stats[stat.nombre] = stat

    def get_stat(self, nombre: str):
        """Valor actual de un stat. KeyError explicito si no existe."""
        return self._stats[nombre].valor

    def set_stat(self, nombre: str, valor) -> None:
        self._stats[nombre].valor = valor

    def tiene_stat(self, nombre: str) -> bool:
        return nombre in self._stats

    def listar_stats(self) -> dict:
        return dict(self._stats)

    def serializar_stats(self) -> dict:
        """Hook de Comportamiento.serializar(): expone el ESTADO actual
        de cada stat, no la lista de instancias iniciales recibida."""
        return {nombre: stat.valor for nombre, stat in self._stats.items()}

    def deserializar_stats(self, value: dict) -> None:
        """
        FIX: hook simétrico de serialize_stats(), que antes no existía.

        reconstruir_elemento() construye el objeto con __new__ (sin pasar
        por __init__), así que este es el ÚNICO punto donde self._stats
        se inicializa para un elemento que llega por red o snapshot. Sin
        este método, Comportamiento.deserializar() no encontraba
        "deserialize_stats" y hacía un setattr(self, "stats", value) a
        secas — dejando self._stats sin existir nunca, y cualquier
        get_stat()/set_stat() posterior reventaba con AttributeError.

        Se reconstruye cada entrada como un Stat "plano" (no como su
        subclase original, p.ej. Armadura) porque aquí solo se dispone
        del par nombre/valor, no de los parámetros de construcción de
        cada Stat_Derivado. Esto es suficiente para get_stat/set_stat,
        pero si recalcular_derivados() se necesita después de un
        roundtrip de red/snapshot, haría falta guardar también la clase
        original de cada stat derivado — no es el caso de bot_id (stat
        "id", simple), pero conviene saberlo si esto se reutiliza para
        stats derivados tras cargar un snapshot.
        """
        self._stats = {
            nombre: Stat(nombre=nombre, valor=valor) for nombre, valor in value.items()
        }

    def recalcular_derivados(self) -> None:
        """
        Recalcula todos los Stat_Derivado, EN EL ORDEN en que se pasaron a
        __init__. Ese orden importa: si un derivado depende de otro derivado
        (p.ej. algo que dependiera de temperatura_optima, que a su vez
        depende de grasa), quien construye la lista en Bot.__init__ debe
        colocar temperatura_optima ANTES que ese otro derivado.
        """
        for stat in self._stats.values():
            if isinstance(stat, Stat_Derivado):
                stat.recalcular()
