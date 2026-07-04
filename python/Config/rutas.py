"""
Config/rutas.py
----------------
Rutas centralizadas de los scripts de arranque de cada componente.

Es la única fuente de verdad sobre "dónde vive cada _server.py" en el
proyecto. Si se reorganiza la estructura de carpetas, este es el único
fichero que hay que tocar.

Usado por:
  - main.py                              (arranque local y producción)
  - Test/Main/test_main_integration.py   (tests de integración)

compile_protos.py NO usa este fichero — define su propio ROOT porque
es una herramienta de build independiente que se ejecuta antes de que
el resto del código sea importable.
"""

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
    / "Gestor_Mundo"
    / "gestor_mundo_server.py"
)
SCRIPT_GESTOR_BOTS = (
    ROOT
    / "Infraestructura"
    / "Gestores"
    / "Bots"
    / "Gestor_Bots"
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
