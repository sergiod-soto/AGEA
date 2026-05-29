"""
compile_protos.py — Alternativa al .sh para Windows.

Compila todos los .proto y corrige los imports relativos.

Uso (desde la raíz del proyecto):
    python compile_protos.py
"""

import pathlib
import re
import subprocess
import sys

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
ROOT      = pathlib.Path(__file__).parent
PROTO_DIR = ROOT / "Hypervisores" / "Transporte" / "Protobufs"
OUT_DIR   = ROOT / "Hypervisores" / "Transporte" / "Proto_Generated"

PROTOS = [
    "common.proto",
    "gestor_bots_service.proto",
    "hypervisor_service.proto",
    "world_proxy_service.proto",
    "log_service.proto",
]

# ---------------------------------------------------------------------------
# 1. Crear carpeta de salida
# ---------------------------------------------------------------------------
OUT_DIR.mkdir(parents=True, exist_ok=True)
print(f"==> Fuentes .proto:  {PROTO_DIR}")
print(f"==> Salida generada: {OUT_DIR}")

# ---------------------------------------------------------------------------
# 2. Compilar cada .proto
# ---------------------------------------------------------------------------
for proto in PROTOS:
    proto_path = PROTO_DIR / proto
    if not proto_path.exists():
        print(f"  [WARN] No encontrado: {proto} — saltando.")
        continue

    print(f"  Compilando {proto} ...")
    result = subprocess.run(
        [
            sys.executable, "-m", "grpc_tools.protoc",
            f"--proto_path={PROTO_DIR}",
            f"--python_out={OUT_DIR}",
            f"--grpc_python_out={OUT_DIR}",
            str(proto_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  [ERROR] {proto}:\n{result.stderr}")
        sys.exit(1)

# ---------------------------------------------------------------------------
# 3. Corregir imports absolutos → relativos en *_pb2_grpc.py
#
# grpc_tools genera:   import common_pb2 as common__pb2
# Necesitamos:         from . import common_pb2 as common__pb2
# ---------------------------------------------------------------------------
print("\n==> Corrigiendo imports relativos en *_pb2.py y *_pb2_grpc.py ...")
pattern = re.compile(r"^import (\w+_pb2)", re.MULTILINE)

# Corregir AMBOS tipos de fichero generados
for pb_file in sorted(OUT_DIR.glob("*_pb2*.py")):
    original = pb_file.read_text(encoding="utf-8")
    fixed    = pattern.sub(r"from . import \1", original)
    if fixed != original:
        pb_file.write_text(fixed, encoding="utf-8")
        print(f"  Corregido: {pb_file.name}")
    else:
        print(f"  Sin cambios: {pb_file.name}")

# ---------------------------------------------------------------------------
# 4. __init__.py para que Proto_Generated sea un paquete importable
# ---------------------------------------------------------------------------
init = OUT_DIR / "__init__.py"
if not init.exists():
    init.touch()
    print(f"\n==> Creado {init}")

# ---------------------------------------------------------------------------
# 5. Resumen
# ---------------------------------------------------------------------------
print("\n==> ¡Compilación completada!")
for f in sorted(OUT_DIR.glob("*_pb2*.py")):
    print(f"    {f.name}")
