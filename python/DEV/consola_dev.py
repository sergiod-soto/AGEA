import code

from Core.Entities.Mundo.mundo import Mundo


def abrir_consola(contexto_local=None):
    """Abre una consola Python interactiva con acceso a las variables locales."""
    variables = globals().copy()
    if contexto_local:
        variables.update(contexto_local)

    code.interact(
        local=variables,
        banner="=== Consola de depuración === (escribe 'exit()' para salir)",
    )


# -----------------------------------------------------------------------------------
variables = {
    "mundo": None,
    "seleccion": None,
}
# -----------------------------------------------------------------------------------


def set_mundo(mundo: Mundo):
    variables["mundo"] = mundo


def crear(): ...


def eliminar(): ...


def seleccionar(id: str): ...
