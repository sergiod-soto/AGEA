# Infraestructura/Gestores/Mundo/Hidrologia/red_fluvial.py
"""
red_fluvial.py - Representación en Grafo Acíclico Dirigido (DAG) de la red fluvial
(ríos, lagos y océano) y motor de simulación de caudales y cotas.
"""

from __future__ import annotations
import logging
from typing import Optional

from Config.parametros_simulacion import (
    ALTURA_CAPA_AIRE,
    EVAPORACION_COEF_BASE,
    EVAPORACION_COEF_VIENTO,
    SEGUNDOS_SIMULADOS_TICK,
    TAMANHO_CELDA_LOGICA,
)
from Config.settings import ATMOSFERA_ESCALA
from Core.Entities.Elementos.Complejos.Lago.Lago import Lago
from Core.Entities.Elementos.Complejos.Oceano.Oceano import Oceano
from Core.Entities.Elementos.Complejos.Rio.Rio import Rio
from Core.Fisica.termodinamica import densidad_vapor_saturacion
from Infraestructura.Gestores.Mundo.Clima.traduccion_malla import terreno_a_clima
from Infraestructura.Gestores.Mundo.Hidrologia.modelos import (
    DatosAtmosferaHidro,
    ResultadoTickHidro,
)

logger = logging.getLogger(__name__)


class RedFluvial:
    """
    Grafo Acíclico Dirigido (DAG) que modela la red hidrológica mundial.
    Procesa tramos de río y cuencas lacustres en orden topológico (de mayor a menor cota).
    """

    # Caudal de manantial por defecto en nacimiento (kg de agua por tick)
    CAUDAL_MANANTIAL_BASE: float = 100.0

    # Margen de histéresis por defecto en metros/cota para evitar oscilación de terreno
    HISTERESIS_COTA_DEFAULT: float = 0.005

    # Fracción de volumen en tránsito que sale de un tramo de río por tick
    FRACCION_TRANSITO_RIO: float = 0.6

    def __init__(self):
        self.rios: dict[int, Rio] = {}
        self.lagos: dict[int, Lago] = {}
        self.oceano: Oceano = Oceano(id_elemento=0)

        # Mapeos directos de celda -> río / lago
        self.celda_a_rio: dict[tuple[int, int], int] = {}
        self.celda_a_lago: dict[tuple[int, int], int] = {}

        # Suelos originales bajo las celdas de agua (para restaurar al secarse)
        self.suelos_originales: dict[tuple[int, int], str] = {}

        # Batimetría / cota de cuenca por lago: id_lago -> [(x, y, elev)] ordenada por elev
        self.perfiles_lagos: dict[int, list[tuple[int, int, float]]] = {}

        # Orden topológico cacheado: lista de claves de nodo ("rio_{id}", "lago_{id}", "oceano")
        self.orden_topologico: list[str] = []

        # Área de una celda de terreno en m²
        self.area_celda_m2: float = float(TAMANHO_CELDA_LOGICA**2)

    def inicializar_desde_red(
        self,
        red: dict,
        hidrologia: dict[tuple[int, int], dict],
        alturas: dict[tuple[int, int], int],
        suelos_originales: Optional[dict[tuple[int, int], str]] = None,
    ) -> None:
        """
        Construye el grafo DAG a partir de los datos generados por CapaRios / CapaMaresInteriores.
        Separa cauce principal (camino) de celdas de ensanchamiento y ordena las
        celdas de lagos por cota batimétrica.
        """
        self.rios.clear()
        self.lagos.clear()
        self.celda_a_rio.clear()
        self.celda_a_lago.clear()
        self.suelos_originales = dict(suelos_originales or {})
        self.perfiles_lagos.clear()

        # 1. Agrupar celdas de hidrología por río y por lago
        celdas_rio_hidro: dict[int, list[tuple[int, int]]] = {}
        celdas_lago_hidro: dict[int, list[tuple[int, int, float]]] = {}

        for pos, info in hidrologia.items():
            tipo = info.get("tipo")
            id_elem = info.get("id")
            if id_elem is None:
                continue

            if tipo == "rio":
                celdas_rio_hidro.setdefault(id_elem, []).append(pos)
                self.celda_a_rio[pos] = id_elem
            elif tipo == "lago":
                elev = float(info.get("elev", alturas.get(pos, 0)))
                celdas_lago_hidro.setdefault(id_elem, []).append((pos[0], pos[1], elev))
                self.celda_a_lago[pos] = id_elem

        # 2. Inicializar Ríos
        for id_rio, datos_rio in red.get("rios", {}).items():
            id_rio_int = int(id_rio)
            camino = [tuple(c) for c in datos_rio.get("camino", [])]
            set_camino = set(camino)

            # Celdas de ensanchamiento: celdas con este id de río que NO son el camino principal
            todas_celdas = celdas_rio_hidro.get(id_rio_int, [])
            ancho_celdas = [c for c in todas_celdas if c not in set_camino]

            # Volumen base: asegura que un cauce recién generado tiene caudal inicial
            cap_base = max(100.0, float(len(camino) * 1000.0))

            rio = Rio(
                id_elemento=id_rio_int,
                nace_de=datos_rio.get("nace_de", ("manantial", None)),
                muere_en=datos_rio.get("muere_en", ("mar", None)),
                camino=camino,
                ancho_celdas=ancho_celdas,
                volumen=cap_base,
                capacidad_base=cap_base,
                activo=True,
            )
            self.rios[id_rio_int] = rio

        # 3. Inicializar Lagos
        for id_lago, datos_lago in red.get("lagos", {}).items():
            id_lago_int = int(id_lago)
            cuenca = celdas_lago_hidro.get(id_lago_int, [])

            # Ordenar las celdas de la cuenca por elevación batimétrica ascendente
            cuenca.sort(key=lambda item: item[2])
            self.perfiles_lagos[id_lago_int] = cuenca

            fondo = float(datos_lago.get("fondo", 0.0))
            cap_max = float(datos_lago.get("capacidad_maxima", fondo))
            area = int(datos_lago.get("area", len(cuenca)))

            # Inicialmente, todas las celdas del lago generado están anegadas
            celdas_inundadas = {(x, y) for x, y, _ in cuenca}

            # Volumen inicial: llena la cubeta hasta capacidad_maxima
            vol_inicial = self._calcular_volumen_cuenca(cuenca, cap_max)

            lago = Lago(
                id_elemento=id_lago_int,
                nace_de_rio=datos_lago.get("nace_de_rio"),
                desagua_en_rio=datos_lago.get("desagua_en_rio"),
                capacidad_maxima=cap_max,
                fondo=fondo,
                area=area,
                volumen=vol_inicial,
                nivel_actual=cap_max,
                celdas_cuenca=cuenca,
            )
            lago.celdas_inundadas = celdas_inundadas
            self.lagos[id_lago_int] = lago

        # 4. Construir Orden Topológico del DAG
        self._construir_orden_topologico()
        logger.info(
            "RedFluvial inicializada: %d ríos, %d lagos, orden topológico: %d nodos.",
            len(self.rios),
            len(self.lagos),
            len(self.orden_topologico),
        )

    def _calcular_volumen_cuenca(
        self, cuenca: list[tuple[int, int, float]], nivel: float
    ) -> float:
        """
        Calcula el volumen teórico retenido en la cubeta (en kg de agua)
        hasta la cota 'nivel'. V = sum((nivel - elev) * area * dens_agua)
        """
        vol = 0.0
        densidad_agua = 1000.0  # kg/m3
        for _, _, elev in cuenca:
            if elev < nivel:
                profundidad = nivel - elev
                vol += profundidad * self.area_celda_m2 * densidad_agua
        # Si la cubeta es plana o el volumen es ínfimo, garantizar un volumen representativo por celda
        if vol <= 0.0 and cuenca:
            vol = float(len(cuenca) * 1000.0)
        return vol

    def _calcular_nivel_desde_volumen(
        self, cuenca: list[tuple[int, int, float]], volumen: float, fondo: float, max_nivel: float
    ) -> float:
        """
        Encuentra por bisección la cota de la lámina de agua correspondiente a 'volumen'.
        """
        if volumen <= 0.0:
            return fondo
        densidad_agua = 1000.0
        v_max = self._calcular_volumen_cuenca(cuenca, max_nivel)
        if volumen >= v_max:
            return max_nivel

        low = fondo
        high = max_nivel
        for _ in range(16):  # 16 iteraciones dan precisión submilimétrica
            mid = (low + high) / 2.0
            v_mid = self._calcular_volumen_cuenca(cuenca, mid)
            if v_mid < volumen:
                low = mid
            else:
                high = mid
        return (low + high) / 2.0

    def _construir_orden_topologico(self) -> None:
        """
        Genera el orden topológico de cálculo aguas arriba -> aguas abajo
        utilizando el algoritmo de Kahn sobre el DAG fluvial.
        """
        adj: dict[str, list[str]] = {}
        in_degree: dict[str, int] = {}

        def _nodo_rio(id_r: int) -> str:
            return f"rio_{id_r}"

        def _nodo_lago(id_l: int) -> str:
            return f"lago_{id_l}"

        # Registrar todos los nodos
        for id_r in self.rios:
            adj[_nodo_rio(id_r)] = []
            in_degree[_nodo_rio(id_r)] = 0
        for id_l in self.lagos:
            adj[_nodo_lago(id_l)] = []
            in_degree[_nodo_lago(id_l)] = 0
        adj["oceano"] = []
        in_degree["oceano"] = 0

        # Crear aristas dirigidas
        for id_r, rio in self.rios.items():
            origen = _nodo_rio(id_r)
            muere_tipo, muere_ref = rio.muere_en[0], rio.muere_en[1]

            if muere_tipo == "confluencia" and muere_ref in self.rios:
                destino = _nodo_rio(muere_ref)
                adj[origen].append(destino)
                in_degree[destino] += 1
            elif muere_tipo == "lago" and muere_ref in self.lagos:
                destino = _nodo_lago(muere_ref)
                adj[origen].append(destino)
                in_degree[destino] += 1
            elif muere_tipo == "mar":
                adj[origen].append("oceano")
                in_degree["oceano"] += 1

        for id_l, lago in self.lagos.items():
            origen = _nodo_lago(id_l)
            if lago.desagua_en_rio is not None and lago.desagua_en_rio in self.rios:
                destino = _nodo_rio(lago.desagua_en_rio)
                adj[origen].append(destino)
                in_degree[destino] += 1

        # Kahn's algorithm
        cola = [n for n, deg in in_degree.items() if deg == 0 and n != "oceano"]
        orden = []
        visitados = set()

        while cola:
            u = cola.pop(0)
            orden.append(u)
            visitados.add(u)
            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0 and v != "oceano":
                    cola.append(v)

        # Añadir nodos restantes por si hubiera componentes o ciclos anómalos
        for n in adj:
            if n not in visitados and n != "oceano":
                orden.append(n)
        orden.append("oceano")
        self.orden_topologico = orden

    def _calcular_evaporacion_dalton(
        self,
        pos_terreno: tuple[int, int],
        datos_atmosfera: dict[tuple[int, int], DatosAtmosferaHidro],
    ) -> float:
        """
        Calcula la evaporación por celda (en kg/tick) según el modelo Dalton.
        E = (A + B·v) · (ρ_sat(T_agua) − ρ_vapor) · tiempo · area
        """
        pos_clima = terreno_a_clima(pos_terreno[0], pos_terreno[1], ATMOSFERA_ESCALA)
        clima = datos_atmosfera.get(pos_clima)
        if clima is None:
            return 0.0

        t_agua = clima.temperatura_suelo
        t_aire = clima.temperatura_aire
        if t_agua <= 0 or t_aire <= 0:
            return 0.0

        vapor = clima.humedad_absoluta
        sat_agua = densidad_vapor_saturacion(t_agua)
        deficit = sat_agua - vapor
        if deficit <= 0.0:
            return 0.0

        velocidad_transferencia = (
            EVAPORACION_COEF_BASE + EVAPORACION_COEF_VIENTO * clima.viento_intensidad
        )
        kg_m2 = velocidad_transferencia * deficit * SEGUNDOS_SIMULADOS_TICK
        sat_aire = densidad_vapor_saturacion(t_aire)
        capacidad_aire = max(0.0, sat_aire - vapor)
        kg_m2 = min(kg_m2, capacidad_aire * ALTURA_CAPA_AIRE)

        return max(0.0, kg_m2 * self.area_celda_m2)

    def _calcular_lluvia_celda(
        self,
        pos_terreno: tuple[int, int],
        datos_atmosfera: dict[tuple[int, int], DatosAtmosferaHidro],
    ) -> float:
        """Devuelve los kg de lluvia recibidos en una celda durante el tick."""
        pos_clima = terreno_a_clima(pos_terreno[0], pos_terreno[1], ATMOSFERA_ESCALA)
        clima = datos_atmosfera.get(pos_clima)
        if clima is None:
            return 0.0
        return max(0.0, clima.precipitacion_kg_m2 * self.area_celda_m2)

    def simular_paso(
        self,
        tick_id: int,
        datos_atmosfera: dict[tuple[int, int], DatosAtmosferaHidro],
        extracciones: Optional[dict[int, float]] = None,
        histeresis: Optional[float] = None,
    ) -> ResultadoTickHidro:
        """
        Ejecuta un tick de la simulación fluvial agregada a lo largo del DAG.
        Devuelve el delta hidrográfico con mutaciones discretas de terreno
        filtradas por histéresis.
        """
        extracciones = extracciones or {}
        margen_hist = (
            histeresis
            if histeresis is not None
            else self.HISTERESIS_COTA_DEFAULT
        )

        resultado = ResultadoTickHidro(tick_id=tick_id)

        # Resetear caudales de entrada del tick actual
        for rio in self.rios.values():
            # Si nace de un manantial, recibe caudal base constante
            if rio.nace_de[0] == "manantial":
                rio.caudal_entrada = self.CAUDAL_MANANTIAL_BASE
            else:
                rio.caudal_entrada = 0.0
            rio.caudal_salida = 0.0

        for lago in self.lagos.values():
            lago.caudal_entrada = 0.0
            lago.caudal_salida = 0.0

        vertido_mar_tick = 0.0

        # Procesar nodos en orden topológico (aguas arriba -> aguas abajo)
        for nodo_id in self.orden_topologico:
            if nodo_id.startswith("rio_"):
                id_rio = int(nodo_id.removeprefix("rio_"))
                rio = self.rios.get(id_rio)
                if rio is None:
                    continue

                # 1. Sumar lluvia sobre todas las celdas del río (camino + ensanchamiento activo)
                celdas_activas = list(rio.camino)
                if rio.volumen > rio.capacidad_base:
                    celdas_activas.extend(rio.ancho_celdas)

                lluvia_total = sum(
                    self._calcular_lluvia_celda(pos, datos_atmosfera)
                    for pos in celdas_activas
                )
                evap_total = sum(
                    self._calcular_evaporacion_dalton(pos, datos_atmosfera)
                    for pos in celdas_activas
                )
                extrac = extracciones.get(id_rio, 0.0)

                # Balance de masa del tramo
                vol_disponible = rio.volumen + rio.caudal_entrada + lluvia_total - evap_total - extrac
                vol_disponible = max(0.0, vol_disponible)

                # Calcular caudal saliente aguas abajo
                if vol_disponible > 0:
                    caudal_salida = vol_disponible * self.FRACCION_TRANSITO_RIO
                    rio.volumen = vol_disponible - caudal_salida
                    rio.caudal_salida = caudal_salida
                    rio.activo = True
                    resultado.rios_activos.append(id_rio)
                else:
                    rio.volumen = 0.0
                    rio.caudal_salida = 0.0
                    rio.activo = False

                # Entregar caudal saliente al nodo receptor
                muere_tipo, muere_ref = rio.muere_en[0], rio.muere_en[1]
                if muere_tipo == "confluencia" and muere_ref in self.rios:
                    self.rios[muere_ref].caudal_entrada += rio.caudal_salida
                elif muere_tipo == "lago" and muere_ref in self.lagos:
                    self.lagos[muere_ref].caudal_entrada += rio.caudal_salida
                elif muere_tipo == "mar":
                    vertido_mar_tick += rio.caudal_salida

            elif nodo_id.startswith("lago_"):
                id_lago = int(nodo_id.removeprefix("lago_"))
                lago = self.lagos.get(id_lago)
                if lago is None:
                    continue

                cuenca = self.perfiles_lagos.get(id_lago, [])
                area_inundada = lago.celdas_inundadas

                # Sumar lluvia de cuenca y restar evaporación sobre superficie anegada
                lluvia_lago = sum(
                    self._calcular_lluvia_celda((x, y), datos_atmosfera)
                    for x, y, _ in cuenca
                )
                evap_lago = sum(
                    self._calcular_evaporacion_dalton(pos, datos_atmosfera)
                    for pos in area_inundada
                )
                extrac_lago = extracciones.get(id_lago, 0.0)

                vol_disponible = lago.volumen + lago.caudal_entrada + lluvia_lago - evap_lago - extrac_lago
                vol_disponible = max(0.0, vol_disponible)

                # Capacidad máxima crítica de la cubeta (cota X de desborde)
                vol_max_desborde = self._calcular_volumen_cuenca(cuenca, lago.capacidad_maxima)

                if vol_disponible > vol_max_desborde:
                    # El lago supera la cota crítica X: DESBORDA por el río emisario
                    excedente = vol_disponible - vol_max_desborde
                    lago.volumen = vol_max_desborde
                    lago.nivel_actual = lago.capacidad_maxima
                    lago.caudal_salida = excedente
                    resultado.lagos_desbordando.append(id_lago)

                    # Activar río emisario aguas abajo si existe
                    if lago.desagua_en_rio is not None and lago.desagua_en_rio in self.rios:
                        self.rios[lago.desagua_en_rio].caudal_entrada += excedente
                else:
                    # El lago retiene el agua por debajo de la cota de desborde (caudal_salida = 0)
                    lago.volumen = vol_disponible
                    lago.caudal_salida = 0.0
                    lago.nivel_actual = self._calcular_nivel_desde_volumen(
                        cuenca, vol_disponible, lago.fondo, lago.capacidad_maxima
                    )

                # Proyección discreta al terreno con histéresis
                # Evita que el nivel oscile continuamente en gRPC
                nivel = lago.nivel_actual
                for cx, cy, c_elev in cuenca:
                    pos = (cx, cy)
                    esta_inundada = pos in lago.celdas_inundadas

                    if not esta_inundada:
                        # Para inundarse debe superar la cota más el margen
                        if nivel >= c_elev + margen_hist:
                            lago.celdas_inundadas.add(pos)
                            resultado.changed_cells.append(
                                {"pos": pos, "suelo": "Suelo_Agua"}
                            )
                    else:
                        # Para secarse debe descender por debajo de la cota menos el margen
                        if nivel < c_elev - margen_hist:
                            lago.celdas_inundadas.remove(pos)
                            suelo_orig = self.suelos_originales.get(pos, "Suelo_Tierra")
                            resultado.changed_cells.append(
                                {"pos": pos, "suelo": suelo_orig}
                            )

            elif nodo_id == "oceano":
                self.oceano.volumen_recibido += vertido_mar_tick
                resultado.caudal_vertido_mar = vertido_mar_tick

        # Estadísticas finales
        resultado.volumen_total_almacenado = (
            sum(r.volumen for r in self.rios.values())
            + sum(l.volumen for l in self.lagos.values())
        )
        return resultado

    def invalidar_seccion(self, tipo: str, id_elem: int) -> None:
        """
        Invalida la topología cacheada de una sección de río o lago cuando un
        evento modifica alturas o bloquea/excava una celda.
        Permite recalcular el descenso de gradiente / priority flood local
        y reenganchar el DAG dinámicamente.
        """
        logger.info("Invalidando sección hidrográfico: %s id=%d", tipo, id_elem)
        # Reconstruir el orden topológico asegurando consistencia del DAG
        self._construir_orden_topologico()

    def serializar(self) -> dict:
        """Serializa el estado completo del grafo hidrográfico."""
        return {
            "rios": {str(k): r.serializar() for k, r in self.rios.items()},
            "lagos": {str(k): l.serializar() for k, l in self.lagos.items()},
            "oceano": self.oceano.serializar(),
            "suelos_originales": {
                f"{x},{y}": s for (x, y), s in self.suelos_originales.items()
            },
            "orden_topologico": list(self.orden_topologico),
        }

    def deserializar(self, datos: dict) -> None:
        """Restaura el estado completo del grafo hidrográfico."""
        self.rios.clear()
        for k_str, r_data in datos.get("rios", {}).items():
            r = Rio(id_elemento=int(k_str))
            r.deserializar(r_data)
            self.rios[int(k_str)] = r
            for pos in r.camino:
                self.celda_a_rio[pos] = int(k_str)
            for pos in r.ancho_celdas:
                self.celda_a_rio[pos] = int(k_str)

        self.lagos.clear()
        for k_str, l_data in datos.get("lagos", {}).items():
            l = Lago(id_elemento=int(k_str))
            l.deserializar(l_data)
            self.lagos[int(k_str)] = l
            self.perfiles_lagos[int(k_str)] = list(l.celdas_cuenca)
            for pos in l.celdas_inundadas:
                self.celda_a_lago[pos] = int(k_str)

        self.oceano.deserializar(datos.get("oceano", {}))
        self.suelos_originales = {
            tuple(map(int, k.split(","))): s
            for k, s in datos.get("suelos_originales", {}).items()
        }
        self.orden_topologico = list(datos.get("orden_topologico", []))
        if not self.orden_topologico and (self.rios or self.lagos):
            self._construir_orden_topologico()
