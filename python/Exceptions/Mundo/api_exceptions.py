class accion_vacia_error(Exception):
    def __init__(self, funcion):
        msg = f"\033[31mUna accion ({funcion}) no puede estar vacia de funciones\033[0m"
        super().__init__(msg)
