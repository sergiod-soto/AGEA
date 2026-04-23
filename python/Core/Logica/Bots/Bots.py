from Utils.Sistema.funciones_csv import leer_csv

# nombre del fichero que contiene la lista de apellidos
nombre_fichero_apellidos = "Mundo/Apellidos.csv"
# apellidos = []
ite_apellidos = 1

apellidos = leer_csv(nombre_fichero_apellidos, ("codigo"))

print("APELLIDOS:")
print(str(apellidos))
print()


def obtener_siguiente_apellido():
    global ite_apellidos
    global apellidos

    if ite_apellidos < len(apellidos):
        apellido = apellidos[ite_apellidos]
        ite_apellidos += 1
        return apellido
    else:
        return 0


# TODO
def mutar_adn(bot):
    pass
