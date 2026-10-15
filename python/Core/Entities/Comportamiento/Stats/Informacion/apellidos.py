# Core/Entities/Comportamiento/Stats/Informacion/apellidos.py


from Core.Entities.Comportamiento.Stats.Informacion.stat_informacion import Stat_Informacion


class Apellidos(Stat_Informacion):
    def __init__(self, apellidos: list, **kwargs):
        super().__init__("apellidos", apellidos, **kwargs)

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"apellidos": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"apellidos": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    def generar_apellidos(ape1, ape2):
        """
        Genera los apellidos del bot a partir de los del padre y la madre
        """

        apellidos = []
        for i in range(int(len(ape1) / 2)):
            apellidos.append(ape1[i])
            apellidos.append(ape2[i])
        return apellidos
