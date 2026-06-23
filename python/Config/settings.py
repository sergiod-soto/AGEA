# Config/settings.py

# ── Modo de ejecución ─────────────────────────────────────────────────────────
DEBUG: bool = True

# ── Conexión con Unity ────────────────────────────────────────────────────────
UNITY_HOST: str = "127.0.0.1"
UNITY_PORT: int = 5069 if DEBUG else 5001

# ── Perfiles ──────────────────────────────────────────────────────────────────
NUM_PERFILES: int = 6
