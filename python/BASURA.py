import json

from Core.Entities.Elementos.Simples.Piedra.piedra import Piedra
from Core.Entities.Elementos.elemento_test import Elemento_Test

p = Piedra(
    id_elemento = 0,
    casilla=(0, 0),
    tamanho=1,
    capa=1,
    peso=5.0,
    coste_empujar=1.0,
    volumen=1.0,
    rgb_base=(120, 120, 121),
    temperatura_propia=20.0,
    tasa_transferencia_temperatura=0.1,
)

print("representacion de Piedra:")
print(json.dumps(p.representacion()))
