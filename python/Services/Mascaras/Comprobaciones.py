import os


def _comprobar_mascara(direccion):
    """comprueba si existe la mascara (png) en la direccion dada"""

    if os.path.exists(direccion):
        return True
    return False


def comprobar_mascaras(perfil):

    ##############################################################
    dir_base_mascaras = os.getcwd() + "/perfiles/" + perfil + "/mascaras/imagenes"
    dir_mascaras = [
        "/desiertos.png",
    ]
    ##############################################################

    if not os.path.isdir(os.getcwd() + "/perfiles/" + perfil):
        print(
            "El directorio '" + (os.getcwd() + "/perfiles/" + perfil) + "' no existe."
        )
        return False

    errores_en_mascaras = []

    # compruebo si esta el png de cada mascara en su sitio
    for ruta in dir_mascaras:
        if not _comprobar_mascara(dir_base_mascaras + ruta):
            errores_en_mascaras.append(ruta)

    if len(errores_en_mascaras) > 0:
        print("- Error encontrando las mascaras (png) de:")
        for error in errores_en_mascaras:
            print("\t" + str(error))
        return errores_en_mascaras
    return True
