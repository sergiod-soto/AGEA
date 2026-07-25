# Tests/Infraestructura/Local/Unitarios/test_log_categorias.py
"""
test_log_categorias.py — Prueba unitaria de log_categorias.categoria():
función pura compartida por log_servicer.py (modo remoto) y
local_logging.py (modo local) para decidir en qué subcarpeta de Logs/
vive cada componente. Si algún día se desincroniza entre ambos modos,
este test lo detecta de inmediato.
"""

from pathlib import Path

import pytest

from Infraestructura.Gestores.Log.log_categorias import categoria


@pytest.mark.unit
@pytest.mark.parametrize(
    "componente, esperado",
    [
        ("gestor_bots", "Bots/Gestor"),
        ("mundo", "Mundo"),
        ("hv_00", "Bots/Hypervisores"),
        ("hv_12", "Bots/Hypervisores"),
        ("sector_0_0", "Mundo/Sectores"),
        ("sector_3_7", "Mundo/Sectores"),
    ],
)
def test_categoria_componentes_conocidos(componente, esperado):
    assert categoria(componente) == Path(esperado)


@pytest.mark.unit
def test_categoria_componente_desconocido_cae_en_raiz():
    """
    Un componente nuevo que no encaje en ningún nombre exacto ni
    prefijo debe caer en la raíz de Logs/ (Path(".")) — quien llama
    (log_servicer/local_logging) es responsable de avisar con un
    warning, no esta función.
    """
    assert categoria("componente_inventado") == Path(".")
