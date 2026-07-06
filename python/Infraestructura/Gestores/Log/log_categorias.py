# Infraestructura/Gestores/Log/log_categorias.py
"""
log_categorias.py — Clasificación de componente → subcarpeta dentro de Logs/.

Compartido por dos consumidores:
  - log_servicer.py: escribe logs recibidos vía pull (modo remoto).
  - local_logging.py: configura logging directo a fichero (modo local).

Antes vivía duplicado dentro de LogServicer; se extrae aquí para que
ambos caminos (local y remoto) usen exactamente el mismo criterio de
carpetas y no puedan desincronizarse.
"""

from __future__ import annotations
from pathlib import Path

# Nombres exactos conocidos. Si un componente nuevo no encaja aquí ni en
# ningún prefijo de abajo, cae en la raíz de Logs/ (ver categoria()) y se
# avisa con un warning para que no pase desapercibido.
_CARPETA_POR_COMPONENTE: dict[str, str] = {
    "gestor_bots": "Bots/Gestor",
    "mundo": "Mundo",
}

# Prefijos para componentes cuyo nombre exacto varía por instancia.
# TODO: cuando el "mundo lógico" y los sectores tengan cada uno su propia
# subcarpeta dentro de Mundo/ (hoy todo "mundo" cae junto), decidir el
# prefijo/nombre definitivo para cada uno.
_PREFIJOS: dict[str, str] = {
    "hv_": "Bots/Hypervisores",
    "sector_": "Mundo/Sectores",
}


def categoria(component: str) -> Path:
    """
    Devuelve la subcarpeta (relativa a la raíz de Logs/) donde debe vivir
    el .log de este componente.

    Devuelve Path(".") si el componente no está en ninguna tabla — quien
    llama a esta función debe avisar (warning) en ese caso, no fallar.
    """
    if component in _CARPETA_POR_COMPONENTE:
        return Path(_CARPETA_POR_COMPONENTE[component])
    for prefijo, carpeta in _PREFIJOS.items():
        if component.startswith(prefijo):
            return Path(carpeta)
    return Path(".")