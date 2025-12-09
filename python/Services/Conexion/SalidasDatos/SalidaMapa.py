import Services.Mascaras.MainMascaras as Mascaras
import Utils.Sistema.CodigosErrores as Codigos_Errores
from Services.Conexion.SalidasDatos.SalidaError import salida_error


def salida_mapa(shared_data, entrada):

    # hay que comprobar si hay error y cual, o no

    errores = Mascaras.errores

    if len(errores) > 0:
        return salida_error(Codigos_Errores.PNGS_NO_ENCONTRADO, errores)

    serializacion = ""
    partes = []
    partes.append("{\n")
    partes.append('"tipo": "mapa",')



    partes.append("\n}<END>")
    serializacion = serializacion.join(partes)
    print("mensaje para unity:\n" + serializacion)
    return serializacion
