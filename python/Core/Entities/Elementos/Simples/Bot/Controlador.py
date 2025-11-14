import csv
import os

# nombre del fichero que contiene la lista de apellidos


nombre_fichero_apellidos = "Apellidos.csv"
apellidos = []
ite_apellidos = 1

ruta_script = os.path.dirname(os.path.abspath(__file__))
ruta_archivo = os.path.join(ruta_script, nombre_fichero_apellidos)

with open(ruta_archivo, newline="", encoding="utf-8") as archivo:
    lector = csv.DictReader(archivo)
    for fila in lector:
        apellidos.append(fila["codigo"])

def obtener_siguiente_apellido():

    global ite_apellidos

    if ite_apellidos < len(apellidos):
        apellido = apellidos[ite_apellidos]
        ite_apellidos += 1
        return apellido
    else:
        return 0