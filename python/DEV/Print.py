def print(str, color="default"):
    """Imprime un texto en consola con el color especificado.

    Args:
        str (str): El texto a imprimir.
        color (str, optional): El color del texto. Puede ser "red", "green", "yellow",
                               "blue", "magenta", "cyan", "white" o "default". Por defecto es "default".
    """
    colores = {
        "default": "\033[0m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
    }

    color_codigo = colores.get(color, colores["default"])
    print(f"{color_codigo}{str}\033[0m")
    