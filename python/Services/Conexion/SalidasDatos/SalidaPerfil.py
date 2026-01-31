def salida_perfil(shared_data, mensaje):
    
    serializacion = ""
    partes = []
        
    if mensaje["peticion"] == "obtener_perfiles":    
        partes.append(__obtener_perfiles())        
        
    partes.append("\n}<END>")
    
    
    
    
    serializacion = serializacion.join(partes)
    return serializacion


def __obtener_perfiles():
    serializacion = ""
    partes = []
    
    partes.append("")
    
    return serializacion.join(partes)
