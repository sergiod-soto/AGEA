# main.py
"""
Orquestador del proyecto. Punto de entrada único para local y producción.

Modos:
  local      — arranca todo el stack (incl. lo que en AWS es remoto)
               como subprocesos en esta máquina, vía bootstrap.py.
  remoto     — lanza la infraestructura real en AWS, vía
               Infraestructura/AWS/remote.py.
  produccion — no lanza nada nuevo; reemplaza este proceso (os.execv)
               por el script del componente indicado. Se usa dentro de
               cada instancia EC2 ya arrancada (ver aws.py._user_data).

Toda la lógica de arranque vive en Infraestructura/Gestores/Bootstrap/
y Infraestructura/AWS/ — este fichero es solo el punto de entrada CLI.

Uso:
  $env:FRESH="true"; python main.py --modo local
  python main.py --modo produccion --componente sector --id sector_0_1 --sesion <id> --bucket <bucket>
"""

import argparse
import logging
import sys

from Config.rutas import ROOT
from Infraestructura.Gestores.Bootstrap import bootstrap


def main() -> None:
    parser = argparse.ArgumentParser(description="Orquestador del proyecto.")
    parser.add_argument(
        "--modo",
        choices=["local", "produccion", "remoto"],
        default="local",
        help="Entorno de ejecución.",
    )
    parser.add_argument(
        "--componente",
        default=None,
        help="(Solo producción) Tipo de componente: sector, logica_mundo, "
        "gestor_mundo, gestor_bots, hypervisor, comunicaciones_remoto.",
    )
    parser.add_argument(
        "--id",
        default=None,
        help="(Solo producción) ID único de esta instancia del componente.",
    )
    parser.add_argument(
        "--sesion",
        default=None,
        help="(Solo producción) ID de sesión de la partida activa.",
    )
    parser.add_argument(
        "--bucket",
        default=None,
        help="(Solo producción) Nombre del bucket S3.",
    )
    parser.add_argument(
        "--escenario",
        default=None,
        help="(Opcional) Nombre del escenario de inicialización a cargar "
        "(ver Escenarios/escenarios.py). Disponible en local y producción.",
    )
    args = parser.parse_args()

    bootstrap.configurar_entorno(args.modo)

    if args.modo == "local":
        bootstrap.ejecutar_modo_local(escenario=args.escenario)

    elif args.modo == "remoto":
        import yaml
        from Infraestructura.AWS.remote import arrancar_remoto

        config_path = ROOT / "config.yaml"
        if not config_path.exists():
            logging.getLogger("main").error("No se encontró config.yaml en %s", ROOT)
            sys.exit(1)
        with open(config_path) as f:
            config = yaml.safe_load(f)
        arrancar_remoto(config)

    else:  # produccion
        if args.componente is None:
            logging.getLogger("main").error(
                "--componente es obligatorio en modo produccion."
            )
            sys.exit(1)
        bootstrap.ejecutar_componente_produccion(args)


if __name__ == "__main__":
    main()
