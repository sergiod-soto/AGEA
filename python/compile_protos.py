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

ROOT      = pathlib.Path(__file__).parent
PROTO_DIR = ROOT / "Gestores" / "Transporte" / "Protobufs"
OUT_DIR   = ROOT / "Gestores" / "Transporte" / "Proto_Generated"

# Grupos: (subcarpeta_proto, subcarpeta_salida, [ficheros])
GROUPS = [
    (
        "Bots", "Bots",
        ["common.proto", "gestor_bots_service.proto",
         "hypervisor_service.proto", "world_proxy_service.proto"],
    ),
    (
        "Sectores", "Sectores",
        ["sector_service.proto", "gestor_mundo_service.proto"],
    ),
    (
        "Otros", "Otros",
        ["log_service.proto"],
    ),
]

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
#     --proto_path apunta a la raíz de Protobufs para que los imports
#     entre protos del mismo grupo funcionen (e.g. common.proto)
# ─────────────────────────────────────────────

for subproto, subout, files in GROUPS:
    proto_subdir = PROTO_DIR / subproto
    out_subdir   = OUT_DIR   / subout

    for fname in files:
        proto_path = proto_subdir / fname
        if not proto_path.exists():
            print(f"  [WARN] No encontrado: {proto_path} — saltando.")
            continue

        print(f"  Compilando {subproto}/{fname} ...")
        result = subprocess.run(
            [
                sys.executable, "-m", "grpc_tools.protoc",
                # proto_path = raíz de Protobufs para resolver imports entre protos
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

        # protoc genera los ficheros en OUT_DIR/<subproto>/ porque el
        # proto_path es PROTO_DIR y el fichero está en subproto/fname.
        # Verificar que el fichero llegó a la subcarpeta correcta.
        generated_stem = fname.replace(".proto", "")
        expected_pb2      = OUT_DIR / subproto / f"{generated_stem}_pb2.py"
        expected_pb2_grpc = OUT_DIR / subproto / f"{generated_stem}_pb2_grpc.py"

        if not expected_pb2.exists():
            print(f"  [ERROR] No se generó: {expected_pb2}")
            sys.exit(1)

# ─────────────────────────────────────────────
#  3. Corregir imports en todos los _pb2*.py generados (recursivo)
#
#  protoc genera imports de la forma:
#    import common_pb2 as common__pb2
#    from Bots import common_pb2 as Bots_dot_common__pb2
#
#  Necesitamos imports relativos al paquete:
#    from . import common_pb2 as common__pb2
#    from Gestores.Transporte.Proto_Generated.Bots import common_pb2 as ...
# ─────────────────────────────────────────────

print("\n==> Corrigiendo imports en *_pb2*.py ...")

# Patrón 1: import simple   →  from . import ...
pattern_simple = re.compile(r"^import (\w+_pb2)", re.MULTILINE)

# Patrón 2: from Bots import X  →  from Gestores.Transporte.Proto_Generated.Bots import X
# Generalizado para cualquier subcarpeta conocida
subcarpetas = [g[1] for g in GROUPS]
pattern_subpkg = re.compile(
    r"^from (" + "|".join(subcarpetas) + r") import (\w+_pb2[^\s]*)",
    re.MULTILINE,
)
BASE_PKG = "Gestores.Transporte.Proto_Generated"

for pb_file in sorted(OUT_DIR.rglob("*_pb2*.py")):
    original = pb_file.read_text(encoding="utf-8")
    fixed    = original

    # Fix 1: import X_pb2 → from . import X_pb2
    fixed = pattern_simple.sub(r"from . import \1", fixed)

    # Fix 2: from Bots import X → from Gestores...Bots import X
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