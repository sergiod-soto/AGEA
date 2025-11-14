import csv
import os


      
def leer_csv(ruta_csv: str, columnas: tuple) -> dict:
    """
    Lee el CSV en `ruta_csv` (ruta absoluta o relativa al directorio del script)
    y devuelve un dict: { nombre_columna: { indice_fila: valor, ... }, ... }.
    - columnas: tupla con los nombres de las columnas a extraer.
    - Índices de fila empiezan en 0.
    """
    ruta_script = os.path.dirname(os.path.abspath(__file__))
    ruta_archivo = ruta_csv if os.path.isabs(ruta_csv) else os.path.join(ruta_script, ruta_csv)

    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"No se encuentra el fichero en: {ruta_archivo}")

    resultado = {col: {} for col in columnas}

    with open(ruta_archivo, newline="", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        for i, fila in enumerate(lector):
            for col in columnas:
                # devuelve None si la columna no existe en esa fila / en el CSV
                resultado[col][i] = fila.get(col)

    return resultado




