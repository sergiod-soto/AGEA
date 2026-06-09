# region Fisico


# ---- Peso -----------------------------
class Peso_Zero(Exception):
    def __init__(self):
        print("\033[31mEl elemento no puede tener peso 0.0\033[0m")


# region Informacion


# ---- Color -----------------------------
class Transparencia_Incorrecta(Exception):
    def __init__(self, transparencia):
        print(
            f"\033[31mTransparencia debe estar entre 0.0 y 1.0. Transparencia actua:{transparencia}\033[0m"
        )


# endregion
