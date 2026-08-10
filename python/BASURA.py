from Core.Entities.Elementos.Simples.Piedra.piedra import Piedra
from Core.Entities.Elementos.elemento_test import Elemento_Test

# requiere, abstractos = Piedra.obtener_requisitos()
#
# print("REQUIERE")
# print(requiere)
# print()
# print("ABSTRACTOS")
# print(abstractos)

elem = Elemento_Test(casilla=(3, 4), id_elemento=1, peso=10.0)
import json
print(json.dumps(elem.representacion(modo="representacion"), indent=2, ensure_ascii=False))

