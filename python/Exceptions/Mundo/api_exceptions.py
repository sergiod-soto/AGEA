class acciones_error(Exception):
    def __init__(self, funcion):
        print(
            f"\033[31mUna accion ({funcion}) no puede ser 'funcion_hv' y 'funcion_mundo' simultaneamente\033[0m"
        )
