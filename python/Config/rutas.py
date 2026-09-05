# Config/rutas.py


from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SCRIPT_SECTOR = (
    ROOT / "Infraestructura" / "Gestores" / "Mundo" / "Sector" / "sector_server.py"
)
SCRIPT_GESTOR_MUNDO = (
    ROOT
    / "Infraestructura"
    / "Gestores"
    / "Mundo"
    / "GestorMundo"
    / "gestor_mundo_server.py"
)
SCRIPT_GESTOR_BOTS = (
    ROOT
    / "Infraestructura"
    / "Gestores"
    / "Bots"
    / "GestorBots"
    / "gestor_bots_server.py"
)
SCRIPT_HYPERVISOR = (
    ROOT
    / "Infraestructura"
    / "Gestores"
    / "Bots"
    / "Hypervisor"
    / "hypervisor_server.py"
)
SCRIPT_LOGICA_MUNDO = (
    ROOT
    / "Infraestructura"
    / "Gestores"
    / "Mundo"
    / "LogicaMundo"
    / "logica_mundo_server.py"
)
SCRIPT_COMUNICACIONES_REMOTO = (
    ROOT
    / "Infraestructura"
    / "Gestores"
    / "Comunicacion"
    / "Remoto"
    / "comunicaciones_remoto_server.py"
)

SCRIPT_CONSOLA = (
    ROOT / "Infraestructura" / "Gestores" / "Consola" / "consola_main.py",
)
