# Services/Conexion_Visualizador/Salida_Datos/salida_error.py


def salida_error(codigo: int | str, datos: str) -> dict:
    return {
        "tipo": "error",
        "codigo": str(codigo),
        "datos": datos,
    }
