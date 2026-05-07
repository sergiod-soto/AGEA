from Core.Entities.Comportamiento.Energetico.combustible import Combustible
from Core.Entities.Comportamiento.Energetico.termico import Termico
from Core.Entities.Comportamiento.Social.social import Social
from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Entities.Comportamiento.Fisico.fisico import Fisico
from Core.Entities.Comportamiento.Temporal.temporal import Temporal
from Core.Entities.Comportamiento.Energetico.energetico import Energetico
from Core.Entities.Comportamiento.Informativo.informativo import Informativo
from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Comportamiento.Stats.Simples.salud import Salud
from Core.Entities.Comportamiento.Stats.stat import Stat
from Core.Entities.Comportamiento.Temporal.temporal import Temporal



Comportamiento.Energetico.Combustible = Combustible
Comportamiento.Energetico.Termico = Termico

class Categorias:
    def __init__(self):
        self.categoria.Energetico = Energetico
        self.categoria.Fisico = Fisico
        self.categoria.Informativo = Informativo
        self.categoria.Interaccion = Interaccion
        self.categoria.Material = Material
        self.categoria.Salud = Salud
        self.categoria.Social = Social
        self.categoria.Stat = Stat
        self.categoria.Temporal = Temporal
        #
        self.categoria
