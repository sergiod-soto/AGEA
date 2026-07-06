"""
compile_protos.py
-----------------
Compila todos los .proto y corrige los imports relativos.
Salida organizada en subcarpetas: Bots/, Sectores/, Otros/

Uso (desde la raíz del proyecto):
    python compile_protos.py
"""

import pathlib
import re
import subprocess
import sys

# ─────────────────────────────────────────────
#  Rutas
# ─────────────────────────────────────────────

ROOT = pathlib.Path(__file__).parent
PROTO_DIR = ROOT / "Infraestructura" / "Gestores" / "Transporte" / "Protobufs"
OUT_DIR = ROOT / "Infraestructura" / "Gestores" / "Transporte" / "Proto_Generated"

# Grupos: (subcarpeta_proto, subcarpeta_salida, [ficheros])
GROUPS = [
    (
        "",  # raiz
        "",
        [
            "common.proto",
        ],
    ),
    (
        "Bots",
        "Bots",
        [
            "gestor_bots_service.proto",
            "hypervisor_service.proto",
            "world_proxy_service.proto",
        ],
    ),
    (
        "Sectores",
        "Sectores",
        [
            "sector_service.proto",
            "gestor_mundo_service.proto",
        ],
    ),
    (
        "Otros",
        "Otros",
        [
            "log_pull_service.proto",
            "log_service.proto",
        ],
    ),
]

BASE_PKG = "Infraestructura.Gestores.Transporte.Proto_Generated"

# ─────────────────────────────────────────────
#  1. Crear carpetas de salida y __init__.py
# ─────────────────────────────────────────────

OUT_DIR.mkdir(parents=True, exist_ok=True)
_init = OUT_DIR / "__init__.py"
if not _init.exists():
    _init.touch()

for _, subout, _ in GROUPS:
    subdir = OUT_DIR / subout
    subdir.mkdir(parents=True, exist_ok=True)
    init = subdir / "__init__.py"
    if not init.exists():
        init.touch()

print(f"==> Fuentes .proto:  {PROTO_DIR}")
print(f"==> Salida generada: {OUT_DIR}")

# ─────────────────────────────────────────────
#  2. Compilar cada grupo
# ─────────────────────────────────────────────

for subproto, subout, files in GROUPS:
    proto_subdir = PROTO_DIR / subproto
    out_subdir = OUT_DIR / subout

    for fname in files:
        proto_path = proto_subdir / fname
        if not proto_path.exists():
            print(f"  [WARN] No encontrado: {proto_path} — saltando.")
            continue

        print(f"  Compilando {subproto or 'raíz'}/{fname} ...")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "grpc_tools.protoc",
                f"--proto_path={PROTO_DIR}",
                f"--python_out={OUT_DIR}",
                f"--grpc_python_out={OUT_DIR}",
                str(proto_path),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"  [ERROR] {fname}:\n{result.stderr}")
            sys.exit(1)

        generated_stem = fname.replace(".proto", "")
        expected_pb2 = OUT_DIR / subproto / f"{generated_stem}_pb2.py"
        if not expected_pb2.exists():
            print(f"  [ERROR] No se generó: {expected_pb2}")
            sys.exit(1)

# ─────────────────────────────────────────────
#  3. Corregir imports en todos los _pb2*.py
#
#  protoc genera imports de la forma:
#    import common_pb2 as common__pb2           ← Pattern 1
#    from Bots import X_pb2 as Bots_dot_X__pb2  ← Pattern 2
#
#  El problema de aplicar "from . import" a ciegas (Pattern 1):
#    Un fichero en Sectores/ que importa common_pb2 (en la raíz) con
#    "from . import common_pb2" busca en Sectores/ y falla.
#
#  Solución: construir un mapa módulo→paquete_absoluto a partir de
#  GROUPS, y generar el import correcto según la ubicación relativa
#  del módulo destino respecto al fichero que lo importa.
# ─────────────────────────────────────────────

print("\n==> Corrigiendo imports en *_pb2*.py ...")

# Mapa: nombre_módulo_pb2 → paquete_absoluto donde vive
_module_pkg: dict[str, str] = {}
for subproto, subout, files in GROUPS:
    pkg = f"{BASE_PKG}.{subout}" if subout else BASE_PKG
    for fname in files:
        stem = fname.replace(".proto", "_pb2")
        _module_pkg[stem] = pkg

# Pattern 1: import simple     → import X_pb2 [as Y]
pattern_simple = re.compile(r"^import (\w+_pb2)", re.MULTILINE)

# Pattern 2: from Subpkg import X → from BASE_PKG.Subpkg import X
subcarpetas = [g[1] for g in GROUPS if g[1]]
pattern_subpkg = re.compile(
    r"^from (" + "|".join(subcarpetas) + r") import (\w+_pb2[^\s]*)",
    re.MULTILINE,
)

for pb_file in sorted(OUT_DIR.rglob("*_pb2*.py")):
    # Determinar el paquete absoluto del fichero actual
    rel_parts = pb_file.relative_to(OUT_DIR).parts
    current_pkg = f"{BASE_PKG}.{rel_parts[0]}" if len(rel_parts) > 1 else BASE_PKG

    original = pb_file.read_text(encoding="utf-8")
    fixed = original

    # Fix Pattern 1:
    # Si el módulo destino está en el mismo paquete → from . import X
    # Si está en otro paquete → from PAQUETE_ABSOLUTO import X
    # Usamos argumento por defecto para capturar current_pkg en el closure.
    def _fix_simple(m: re.Match, _cur: str = current_pkg) -> str:
        mod = m.group(1)
        target_pkg = _module_pkg.get(mod, BASE_PKG)
        if target_pkg == _cur:
            return f"from . import {mod}"
        return f"from {target_pkg} import {mod}"

    fixed = pattern_simple.sub(_fix_simple, fixed)

    # Fix Pattern 2: from Bots import X → from BASE_PKG.Bots import X
    fixed = pattern_subpkg.sub(
        lambda m: f"from {BASE_PKG}.{m.group(1)} import {m.group(2)}",
        fixed,
    )

    if fixed != original:
        pb_file.write_text(fixed, encoding="utf-8")
        print(f"  Corregido: {pb_file.relative_to(ROOT)}")
    else:
        print(f"  Sin cambios: {pb_file.relative_to(ROOT)}")

# ─────────────────────────────────────────────
#  4. Resumen
# ─────────────────────────────────────────────

print("\n==> ¡Compilación completada!")
for f in sorted(OUT_DIR.rglob("*_pb2*.py")):
    print(f"    {f.relative_to(ROOT)}")
