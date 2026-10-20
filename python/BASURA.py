# BASURA.py (pruebas generales)


# Mide el JSON de un suelo serializado y estima el mensaje de un Sector.
import json
from Core.Entities.Mundo.Suelo.suelo_tierra import Suelo_Tierra

suelo = Suelo_Tierra(casilla=(0, 0), id_elemento=1)
n = len(json.dumps(suelo.serializar()).encode())
print(f"{n} bytes/suelo -> {n * 1600 / 1e6:.2f} MB por Sector")

