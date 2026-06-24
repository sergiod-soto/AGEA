# Services/Conexion_Visualizador/salida_actualizacion.py

from Services.Serializaciones.actualizacion import serializacion_actualizacion


def salida_actualizacion(shared_data) -> dict:
    return serializacion_actualizacion(shared_data)
