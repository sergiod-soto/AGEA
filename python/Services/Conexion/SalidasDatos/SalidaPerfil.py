from Utils.Ficheros.LeerJSON import leer_JSON_Datos


def salida_perfil(shared_data, mensaje):

    serializacion = ""
    partes = []
    if mensaje["peticion"] != "perfil":
        return
    if mensaje["tipo"] == "obtener_perfiles":
        partes.append("{\n")
        partes.append('"peticion": "perfil"')
        partes.append(",\n")
        partes.append('"tipo": "obtener_perfiles",\n')
        partes.append('"perfiles": [\n')
        partes.append(_obtener_perfiles())
        partes.append("\n]\n}")
        partes.append("<END>")

    serializacion = serializacion.join(partes)

    return serializacion


def _obtener_perfiles():

    serializacion = ""
    partes = []

    partes.append(_obtener_perfil(1))
    partes.append(",\n")
    partes.append(_obtener_perfil(2))
    partes.append(",\n")
    partes.append(_obtener_perfil(3))
    partes.append(",\n")
    partes.append(_obtener_perfil(4))
    partes.append(",\n")
    partes.append(_obtener_perfil(5))
    partes.append(",\n")
    partes.append(_obtener_perfil(6))

    serializacion = serializacion.join(partes)

    return serializacion


def _obtener_perfil(perfil_num):

    perfil = leer_JSON_Datos(perfil_num)

    print("perfil leido:", perfil)

    serializacion = ""
    partes = []

    partes.append("{")
    partes.append(f'"id": "{perfil["id"]}"')
    partes.append(",\n")
    partes.append(f'"nombre": "{perfil["nombre"]}"')
    partes.append(",\n")
    partes.append(f'"fecha": "{perfil["fecha"]}"')
    partes.append(",\n")
    partes.append(f'"tiempo_entrenamiento": {perfil["tiempo_entrenamiento"]}')
    partes.append("}")

    serializacion = serializacion.join(partes)

    print(f"__obtener_perfil {perfil_num}:\n{serializacion}")

    return serializacion
