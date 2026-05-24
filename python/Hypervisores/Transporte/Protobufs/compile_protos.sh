#!/usr/bin/env bash
# compile_protos.sh
#
# Compila todos los .proto a módulos Python y los guarda en una
# carpeta separada (Proto_Generated), limpia de fuentes .proto.
#
# Estructura resultante:
#   Hypervisores/Transporte/
#   ├── Protobufs/            ← fuentes .proto (este directorio)
#   │   └── compile_protos.sh
#   └── Proto_Generated/      ← módulos Python generados
#       ├── __init__.py
#       ├── common_pb2.py
#       ├── common_pb2_grpc.py
#       ├── gestor_service_pb2.py
#       ├── gestor_service_pb2_grpc.py
#       ├── hypervisor_service_pb2.py
#       ├── hypervisor_service_pb2_grpc.py
#       ├── world_proxy_service_pb2.py
#       └── world_proxy_service_pb2_grpc.py
#
# Dependencias:
#   pip install grpcio grpcio-tools
#
# Uso:
#   cd Hypervisores/Transporte/Protobufs
#   chmod +x compile_protos.sh
#   ./compile_protos.sh

set -euo pipefail

# Directorio de los .proto fuente (donde está este script)
PROTO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Carpeta de salida: hermana de Protobufs, dentro de Transporte
OUT_DIR="$(cd "$PROTO_DIR/.." && pwd)/Proto_Generated"

echo "==> Fuentes .proto:    $PROTO_DIR"
echo "==> Salida generada:   $OUT_DIR"

# Crear la carpeta de salida si no existe
mkdir -p "$OUT_DIR"

# Lista de protos en orden de dependencia (common primero)
PROTOS=(
  common.proto
  gestor_service.proto
  hypervisor_service.proto
  world_proxy_service.proto
)

for PROTO in "${PROTOS[@]}"; do
  if [[ ! -f "$PROTO_DIR/$PROTO" ]]; then
    echo "  [WARN] No encontrado: $PROTO — saltando."
    continue
  fi

  echo "  Compilando $PROTO ..."
  python -m grpc_tools.protoc \
    --proto_path="$PROTO_DIR" \
    --python_out="$OUT_DIR" \
    --grpc_python_out="$OUT_DIR" \
    "$PROTO_DIR/$PROTO"
done

# Corregir imports absolutos → relativos en los *_pb2_grpc.py generados.
# grpc_tools genera: import common_pb2 as common__pb2
# Necesitamos:       from . import common_pb2 as common__pb2
echo "==> Corrigiendo imports relativos en *_pb2_grpc.py ..."
for GRPC_FILE in "$OUT_DIR"/*_pb2_grpc.py; do
  [[ -f "$GRPC_FILE" ]] || continue
  if [[ "$(uname)" == "Darwin" ]]; then
    sed -i '' 's/^import \(.*_pb2\)/from . import \1/' "$GRPC_FILE"
  else
    sed -i 's/^import \(.*_pb2\)/from . import \1/' "$GRPC_FILE"
  fi
  echo "  Corregido: $(basename "$GRPC_FILE")"
done

# __init__.py para que Proto_Generated sea un paquete Python importable
INIT="$OUT_DIR/__init__.py"
if [[ ! -f "$INIT" ]]; then
  touch "$INIT"
  echo "==> Creado $INIT"
fi

echo ""
echo "==> ¡Compilación completada!"
echo "    Archivos generados en: $OUT_DIR"
ls "$OUT_DIR"/*_pb2*.py 2>/dev/null | sed 's|.*/||' | sed 's/^/    /'
