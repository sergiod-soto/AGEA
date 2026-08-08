from Core.Entities.Elementos.Simples.Piedra.piedra import Piedra

requiere, abstractos = Piedra.obtener_requisitos()


# print("REQUIERE")
# print(requiere)
# print()
# print("ABSTRACTOS")
# print(abstractos)

p = Piedra(
    id_elemento=0,
    tamanho=1,
    casilla=(0, 0),
    capa=1,
    peso=1,
    coste_empujar=1,
    volumen=1,
    rgb_base=(0, 0, 0),
    durabilidad_max_destruible=1,
    temperatura_propia=1,
    tasa_transferencia_temperatura=1,
    durabilidad_max_erosion=1,
)

print(p.serializar(modo="representacion"))
