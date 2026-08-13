#!/usr/bin/env python3
# Scripts/generar_stubs_unity.py
"""
Compila los .proto del lado Python a stubs C# para el proyecto Unity.

protoc y grpc_csharp_plugin NO se buscan en NuGetForUnity ni en el
sistema: NuGetForUnity está pensado para dependencias de RUNTIME
(librerías que el juego referencia), no para herramientas de build
como protoc -- por eso Grpc.Tools no se resolvía ahí (confirmado: ni
siquiera llegó a bajarse a la caché global de NuGet).

En vez de depender de eso, este script descarga el paquete Grpc.Tools
directamente desde nuget.org (es un .zip normal bajo otro nombre) la
primera vez que se ejecuta, lo cachea en disco, y usa el protoc /
grpc_csharp_plugin que trae dentro. Ejecuciones siguientes reusan la
caché -- no vuelve a descargar nada salvo que borres la carpeta de
caché o cambies GRPC_TOOLS_VERSION.

Fuente única de los .proto: siguen viviendo solo en la carpeta Python
(no se copian ni se duplican) -- este script es el único puente entre
ambos lados, para que no puedan divergir por edición manual en Unity.

No depende de dónde coloques el script dentro de AGEA (Assets/Scripts
de Unity, una carpeta de herramientas aparte, o donde sea): se
autolocaliza subiendo desde su propia ubicación hasta encontrar la
carpeta que tiene como hijas directas 'python' y 'unity' (sin
importar mayúsculas), y desde ahí construye el resto de rutas.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

# Versión de Grpc.Tools a usar -- fijada a la misma que Grpc.Core.Api
# que ya tienes instalado (2.83.0), para evitar que el protoc que
# compila y las librerías runtime del proyecto queden desincronizadas.
# Si actualizas Grpc.Core.Api/Grpc.Net.Client más adelante, actualiza
# esto también.
GRPC_TOOLS_VERSION = "2.83.0"

# Subcarpeta real donde viven los .proto dentro de la carpeta Python
# (confirmada: incluye "Gestores").
RUTA_PROTOS_DESDE_PYTHON = ("Infraestructura", "Gestores", "Transporte", "Protobufs")


def _hijo_case_insensitive(padre: Path, nombre: str) -> Path | None:
    """Busca una subcarpeta por nombre sin importar mayúsculas/minúsculas."""
    if not padre.exists():
        return None
    for hijo in padre.iterdir():
        if hijo.is_dir() and hijo.name.lower() == nombre.lower():
            return hijo
    return None


def _encontrar_raiz_agea(inicio: Path) -> Path:
    """
    Sube desde 'inicio' hasta encontrar una carpeta con hijas directas
    'python' y 'unity' -- esa es la raíz de AGEA. Evita depender de una
    ruta relativa fija por dónde viva el script.
    """
    actual = inicio
    for _ in range(10):
        if _hijo_case_insensitive(actual, "python") and _hijo_case_insensitive(
            actual, "unity"
        ):
            return actual
        if actual.parent == actual:
            break
        actual = actual.parent
    sys.exit(
        f"No se encontró una carpeta con subcarpetas 'python' y 'unity' "
        f"subiendo desde {inicio}. ¿Está el script dentro del árbol de AGEA?"
    )


RAIZ_AGEA = _encontrar_raiz_agea(Path(__file__).resolve().parent)
_CARPETA_PYTHON = _hijo_case_insensitive(RAIZ_AGEA, "python")
_CARPETA_UNITY_RAIZ = _hijo_case_insensitive(RAIZ_AGEA, "unity")

CARPETA_PROTOS = _CARPETA_PYTHON.joinpath(*RUTA_PROTOS_DESDE_PYTHON)
CARPETA_UNITY = _CARPETA_UNITY_RAIZ
CARPETA_SALIDA = CARPETA_UNITY / "Assets" / "Scripts" / "ProtoGenerated"

# Caché de Grpc.Tools descargado -- deliberadamente FUERA de Assets/ para
# que Unity no lo trate como parte del proyecto, y fuera de Python/ para
# que quede claro que es tooling de build, no código de ninguno de los dos
# lados. Añadir a .gitignore: no debería versionarse (se puede
# regenerar/descargar en cualquier máquina).
CARPETA_CACHE = RAIZ_AGEA / ".cache" / "grpc-tools" / GRPC_TOOLS_VERSION


def _sufijo_plataforma() -> str:
    sistema = platform.system()
    if sistema == "Windows":
        return "windows_x64"
    if sistema == "Darwin":
        return "macosx_x64"
    return "linux_x64"


def _asegurar_grpc_tools_descargado() -> Path:
    """
    Descarga y extrae el paquete Grpc.Tools si no está ya en caché.
    Devuelve la carpeta 'tools/' extraída (contiene una subcarpeta por
    plataforma: windows_x64/, linux_x64/, macosx_x64/...).
    """
    carpeta_tools = CARPETA_CACHE / "tools"
    if carpeta_tools.exists():
        return carpeta_tools  # ya descargado en una ejecución anterior

    CARPETA_CACHE.mkdir(parents=True, exist_ok=True)
    url = f"https://www.nuget.org/api/v2/package/Grpc.Tools/{GRPC_TOOLS_VERSION}"
    zip_temporal = CARPETA_CACHE / "grpc-tools.nupkg.zip"

    print(
        f"Descargando Grpc.Tools {GRPC_TOOLS_VERSION} desde nuget.org (solo la primera vez)..."
    )
    try:
        urllib.request.urlretrieve(url, zip_temporal)
    except Exception as ex:
        sys.exit(
            f"No se pudo descargar Grpc.Tools desde {url}: {ex}\n"
            f"Comprueba conexión a internet o si GRPC_TOOLS_VERSION="
            f"'{GRPC_TOOLS_VERSION}' existe en https://www.nuget.org/packages/Grpc.Tools"
        )

    with zipfile.ZipFile(zip_temporal) as z:
        z.extractall(CARPETA_CACHE)
    zip_temporal.unlink()

    if not carpeta_tools.exists():
        sys.exit(
            f"Se descargó el paquete pero no apareció la carpeta esperada: {carpeta_tools}"
        )

    return carpeta_tools


def _localizar_binario(carpeta_tools: Path, nombre_base: str) -> Path:
    sufijo = _sufijo_plataforma()
    extension = ".exe" if platform.system() == "Windows" else ""
    ruta = carpeta_tools / sufijo / f"{nombre_base}{extension}"
    if not ruta.exists():
        sys.exit(f"No se encontró {ruta} dentro del paquete Grpc.Tools descargado.")

    # En Linux/Mac el bit de ejecución no siempre sobrevive a la extracción
    # del zip -- sin esto, subprocess.run fallaría con 'Permission denied'.
    if platform.system() != "Windows":
        ruta.chmod(ruta.stat().st_mode | 0o111)

    return ruta


def main() -> None:
    carpeta_tools = _asegurar_grpc_tools_descargado()
    protoc = _localizar_binario(carpeta_tools, "protoc")
    plugin = _localizar_binario(carpeta_tools, "grpc_csharp_plugin")

    if not CARPETA_PROTOS.exists():
        sys.exit(f"No existe la carpeta de .proto: {CARPETA_PROTOS}")

    protos = sorted(CARPETA_PROTOS.rglob("*.proto"))
    if not protos:
        sys.exit(f"No se encontraron .proto dentro de {CARPETA_PROTOS}")

    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)

    comando = [
        str(protoc),
        f"--proto_path={CARPETA_PROTOS}",
        f"--csharp_out={CARPETA_SALIDA}",
        f"--grpc_out={CARPETA_SALIDA}",
        f"--plugin=protoc-gen-grpc={plugin}",
        *[str(p) for p in protos],
    ]

    print(f"protoc:              {protoc}")
    print(f"grpc_csharp_plugin:  {plugin}")
    print(f"Salida:              {CARPETA_SALIDA}")
    print("Compilando:")
    for p in protos:
        print(f"  - {p.relative_to(CARPETA_PROTOS)}")
    print()

    resultado = subprocess.run(comando)
    if resultado.returncode != 0:
        sys.exit("protoc falló -- revisa el error de arriba.")

    print(f"OK -- stubs generados en {CARPETA_SALIDA}")
    print("Unity los detectará solos al volver al Editor (o Assets > Refresh).")


if __name__ == "__main__":
    main()
