def salida_error(codigo, datos):
    serializacion = ""
    partes = []
    partes.append("{\n")
    partes.append('"tipo": "error",')
    partes.append('"codigo":"' + str(codigo) + '",')
    partes.append('"datos":"' + datos + '"')
    partes.append("\n}<END>")
    serializacion = serializacion.join(partes)
    return serializacion
