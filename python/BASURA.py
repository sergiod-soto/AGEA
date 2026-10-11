# BASURA.py (prueba de round-trip del Bot)
import json

from Core.Entities.Elementos.Simples.Bot.bot import Bot
from Core.Entities.Elementos.registry import reconstruir_elemento

stats_script = {
    "armadura": 0,
    "grasa": 0,
    "longevidad": 0,
    "movilidad": 0,
    "percepcion": 0,
}

b = Bot(
    id_elemento=101,
    stats_script=stats_script,
    id_bot=7,
    tamanho=1,
    casilla=(3, 4),
    rotacion=0,
)

# Esta línea es la que usa el serializar() de Bot que sigue vigente:
# si falla aquí, confirma el problema que describí (falta __clase__, self.adn...).
datos = b.serializar()
print(datos)

b2 = reconstruir_elemento(json.loads(json.dumps(datos)))
assert b2.get_stat("id") == 7 and b2.casilla == (3, 4)
print("round-trip OK")
