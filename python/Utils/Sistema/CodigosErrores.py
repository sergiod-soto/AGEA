"""
Docstring for Utils.Sistema.CodigosErrores

Listado de codigos de errores

Explicacion:

1xxxx - Errores de conexión / red
    Los producidos por sockets, TCP, timeouts, desconexiones.

2xxxx - Errores de datos enviados por Python
    Formateo, JSON inválido, tipos incorrectos, campos faltantes.

3xxxx - Errores de mundo / mapas
    Problemas con PNG, generación de biomas, integridad, carga, etc.

4xxxx - Errores de bots / simulación
    Errores de IA, cálculos internos, límites del mundo, etc.

5xxxx - Errores de sincronización
    Desfase entre Python-Unity, ticks, paquetes fuera de orden.

6xxxx - Errores de servidor Python
    Excepciones internas, fallos al generar datos o procesos.

7xxxx - Errores de cliente Unity
    Fallos al interpretar datos, errores de lógica local.

9xxxx - Errores críticos
    Casos graves que requieren parar simulación.
"""

PNGS_NO_ENCONTRADO = 3000
PNGS_CORRUPTOS = 3010
DISCREPANCIA_HASH_PNG = 3020
DISCREPANCIA_HASH_CONTROL = 3030
