# Core/Entities/Mundo/Atmosfera/celda_atmosfera.py

from vectors import Vector2

from Config.parametros_simulacion import ALTURA_CAPA_AIRE, CALOR_LATENTE_VAPORIZACION
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.temperatura_atmosferica import (
    TemperaturaAtmosferica,
)
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.presion import (
    Presion,
)
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.viento import (
    Viento,
)
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.humedad_absoluta import (
    Humedad_Absoluta,
)
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Derivado.humedad_relativa import (
    Humedad_Relativa,
)

# Únicos campos que aplicar_patch puede cambiar: propiedades simples de
# terreno. Lista BLANCA: todo lo demás (magnitudes, cachés, radiación,
# posición...) tiene estado interno propio y se cambia por su método
# específico. Un campo de terreno nuevo hay que añadirlo aquí a propósito.
_CAMPOS_PATCH_PERMITIDOS = frozenset({"viento_objetivo"})


class Celda_Atmosfera:

    def __init__(
        self,
        posicion: tuple[int, int],
        viento_objetivo: Vector2,
    ) -> None:
        self.posicion = posicion

        # Radiación (W/m²): se recalcula cada tick en sistema_atmosferico;
        # es un float simple, sin clase propia.
        self.radiacion: float = 0.0

        # Magnitudes: cada una es un Sistema_Atmosferico con su estado y su
        # actualizar(). Se usan los valores iniciales por defecto de cada
        # clase (temperatura en K, presión en Pa): NO pasar números sueltos
        # aquí, porque las unidades son fáciles de confundir.
        self.temperatura = TemperaturaAtmosferica()
        self.presion = Presion()
        self.viento = Viento()
        self.humedad_absoluta = Humedad_Absoluta()
        self.humedad_relativa = Humedad_Relativa()

        # m/s. Velocidad hacia la que se relaja el viento (rozamiento). Es
        # propiedad del TERRENO: la fuente de verdad es Logica; el Sector la
        # recibe en LoadState y por parche (fase 0).
        self.viento_objetivo = viento_objetivo

        # ---- Caché de Suelo (térmica) ----
        # Valores de cada Suelo cubierto por esta celda, por posición, para
        # recalcular de forma incremental cuando cambia UN Suelo sin releer
        # todos los del bloque.
        self._tasas_conversion_por_suelo: dict[tuple[int, int], float] = {}
        self._inercias_por_suelo: dict[tuple[int, int], float] = {}

        # Sumas mantenidas en paralelo: la media sale en O(1).
        self._suma_tasas: float = 0.0
        self._suma_inercias: float = 0.0

        # Medias públicas: lo que consulta Temperatura.actualizar. Valen 0.0
        # mientras no haya ningún Suelo (Temperatura lo rechaza con
        # ValueError, a propósito: mejor fallar que simular con basura).
        self.tasa_conversion_radiacion_calor: float = 0.0
        self.inercia_termica: float = 0.0

        # ---- Caché de resistencia al viento ----
        # No es propiedad de la celda sino de los elementos del sector; se
        # cachea aquí solo por necesidad de cálculo. Indexado por id_elemento
        # (no por posición): varios elementos pueden aportar resistencia
        # desde la MISMA posición.
        self._resistencias_por_elemento: dict[int, float] = {}

        # Producto de (1 - r_i) de los elementos con r_i < 1 (bloqueo
        # parcial). Siempre > 0, así que es reversible dividiendo.
        self._producto_paso_libre: float = 1.0

        # Cuántos elementos con r_i == 1.0 (bloqueo total; comparación exacta
        # porque son valores definidos a mano) hay en esta celda. Contador y
        # no bool: si dos bloqueantes solapan y uno desaparece, el otro debe
        # seguir bloqueando.
        self._contador_bloqueo_total: int = 0

        # Valores públicos. Se mira SIEMPRE bloqueo_total_viento primero; solo
        # si es False tiene sentido mirar resistencia_viento (con bloqueo
        # total, ese valor describe solo a los elementos no bloqueantes).
        self.bloqueo_total_viento: bool = False
        self.resistencia_viento: float = 0.0

    # ------------------------------------------------------------------
    # Suelo
    # ------------------------------------------------------------------

    def registrar_suelo(
        self,
        posicion_suelo: tuple[int, int],
        tasa_conversion: float,
        inercia: float,
    ) -> None:
        """
        Alta de un Suelo. ValueError si esa posición ya tiene uno: un Suelo
        nunca se elimina, solo se sustituye (actualizar_suelo).
        `inercia` es la masa térmica del SUELO de esa casilla,
        en J/(m²·K), sin el aire.
        El Suelo convierte radiación en calor (tasa) y es la batería que frena
        el calentamiento y el enfriamiento del suelo de la celda.
        La validación de rangos (tasa en [0, 100], inercia > 0) vive en
        Suelo.__init__ y, como red de seguridad, en Temperatura.actualizar.
        """
        if posicion_suelo in self._tasas_conversion_por_suelo:
            raise ValueError(
                f"Ya hay un Suelo registrado en {posicion_suelo}; usa "
                f"actualizar_suelo() para sustituirlo."
            )
        self._tasas_conversion_por_suelo[posicion_suelo] = tasa_conversion
        self._inercias_por_suelo[posicion_suelo] = inercia
        self._suma_tasas += tasa_conversion
        self._suma_inercias += inercia
        self._recalcular_medias()

    def actualizar_suelo(
        self,
        posicion_suelo: tuple[int, int],
        tasa_conversion: float,
        inercia: float,
    ) -> None:
        """
        Sustituye el Suelo de una posición. KeyError si no existía: señal de
        un hook mal enganchado, no algo a silenciar. Se ajustan las sumas con
        la diferencia (nuevo - viejo) en vez de recorrer el dict.
        """
        tasa_vieja = self._tasas_conversion_por_suelo[posicion_suelo]
        inercia_vieja = self._inercias_por_suelo[posicion_suelo]
        self._tasas_conversion_por_suelo[posicion_suelo] = tasa_conversion
        self._inercias_por_suelo[posicion_suelo] = inercia
        self._suma_tasas += tasa_conversion - tasa_vieja
        self._suma_inercias += inercia - inercia_vieja
        self._recalcular_medias()

    def _recalcular_medias(self) -> None:
        n = len(self._tasas_conversion_por_suelo)
        if n == 0:
            # Sin Suelos: todo a cero exacto (evita arrastrar el error de
            # redondeo de las sumas incrementales). Temperatura lo rechaza
            # con ValueError: mejor fallar que simular sin masa térmica.
            self._suma_tasas = 0.0
            self._suma_inercias = 0.0
            self.tasa_conversion_radiacion_calor = 0.0
            self.inercia_termica = 0.0
            return
        self.tasa_conversion_radiacion_calor = self._suma_tasas / n

        # Media de la masa térmica del SUELO de las casillas de la celda. El
        # aire no entra aquí: su capacidad (C_AIRE) se cuenta aparte en
        # TemperaturaAtmosferica.
        self.inercia_termica = self._suma_inercias / n

    # ------------------------------------------------------------------
    # Resistencia al viento
    # ------------------------------------------------------------------

    @staticmethod
    def _validar_resistencia(resistencia: float) -> None:
        # Fuera de [0, 1] el producto de paso libre podría ser 0 o negativo y
        # dejaría de ser reversible por división.
        if not 0.0 <= resistencia <= 1.0:
            raise ValueError(
                f"resistencia_viento debe estar en [0, 1] (recibido {resistencia})."
            )

    def registrar_resistencia_elemento(
        self, id_elemento: int, resistencia: float
    ) -> None:
        """
        Alta de la contribución de un elemento a la resistencia al viento.
        resistencia == 1.0 (exacto) es bloqueo total; el resto entra en el
        producto de paso libre.
        """
        self._validar_resistencia(resistencia)
        if id_elemento in self._resistencias_por_elemento:
            raise ValueError(
                f"Elemento {id_elemento} ya registrado en esta celda de "
                f"atmósfera para resistencia_viento; usa "
                f"actualizar_resistencia_elemento() para un cambio de valor."
            )
        self._resistencias_por_elemento[id_elemento] = resistencia
        if resistencia == 1.0:
            self._contador_bloqueo_total += 1
        else:
            self._producto_paso_libre *= 1.0 - resistencia
        self._recalcular_resistencia_viento()

    def eliminar_resistencia_elemento(self, id_elemento: int) -> None:
        """
        Baja de un elemento (eliminado o movido fuera de esta celda).
        KeyError si no estaba registrado (hook mal enganchado).
        """
        resistencia = self._resistencias_por_elemento.pop(id_elemento)
        if resistencia == 1.0:
            self._contador_bloqueo_total -= 1
        else:
            # Reversible: el producto nunca es 0 (los r == 1.0 no entran).
            self._producto_paso_libre /= 1.0 - resistencia
        if not self._resistencias_por_elemento:
            # Vacío: se restaura el 1.0 exacto, sin residuo de redondeo.
            self._producto_paso_libre = 1.0
        self._recalcular_resistencia_viento()

    def actualizar_resistencia_elemento(
        self, id_elemento: int, nueva_resistencia: float
    ) -> None:
        """Cambio de valor de un elemento ya registrado (p. ej. cambió su
        tipo por transformación, sin cambiar de posición ni de id)."""
        # Se valida ANTES de eliminar: si el valor es inválido, el estado
        # anterior queda intacto en vez de perder el elemento a medias.
        self._validar_resistencia(nueva_resistencia)
        self.eliminar_resistencia_elemento(id_elemento)
        self.registrar_resistencia_elemento(id_elemento, nueva_resistencia)

    def _recalcular_resistencia_viento(self) -> None:
        self.bloqueo_total_viento = self._contador_bloqueo_total > 0
        # _producto_paso_libre se mantiene por multiplicación/división
        # incremental y arrastra error de redondeo (puede quedar en
        # 1.0000000001). Sin recorte, la resistencia saldría ligeramente
        # negativa y el viento se amplificaría (1 - r > 1). Se recorta a [0, 1].
        self.resistencia_viento = max(0.0, min(1.0, 1.0 - self._producto_paso_libre))

    # ------------------------------------------------------------------
    # Evaporación
    # ------------------------------------------------------------------

    def aplicar_evaporacion(self, kg_por_m2_celda: float) -> None:
        """
        Pasa agua del suelo al aire. `kg_por_m2_celda` es la masa evaporada en
        este tick POR m² DE CELDA (no de casilla: quien llama ya repartió la
        casilla entre las casillas de la celda).

          - Aire: la humedad sube kg/ALTURA_CAPA_AIRE (kg/m³).
          - Suelo: se enfría por calor latente, ΔT = L·kg / inercia_termica.
            Usa la inercia media del suelo de la celda, no la del aire.

        ValueError si no hay Suelo registrado (inercia 0): mismo criterio que
        Temperatura.actualizar, mejor fallar que dividir por cero.
        """
        if self.inercia_termica <= 0:
            raise ValueError(
                "aplicar_evaporacion: celda de atmósfera sin Suelo registrado."
            )
        self.humedad_absoluta.valor += kg_por_m2_celda / ALTURA_CAPA_AIRE
        self.temperatura.valor_suelo -= (
            CALOR_LATENTE_VAPORIZACION * kg_por_m2_celda / self.inercia_termica
        )

    # ------------------------------------------------------------------
    # Patch genérico
    # ------------------------------------------------------------------

    def aplicar_patch(self, patch: dict) -> None:
        """
        setattr plano SOLO para los campos de _CAMPOS_PATCH_PERMITIDOS.
        Se valida TODO el patch antes de aplicar nada: si un campo no está
        permitido (o es un typo) se rechaza entero y la celda queda intacta.
        No valida el tipo de los valores (se espera Vector2).
        """
        no_permitidos = sorted(set(patch) - _CAMPOS_PATCH_PERMITIDOS)
        if no_permitidos:
            raise ValueError(
                f"Campos no modificables vía aplicar_patch: {no_permitidos}. "
                f"Permitidos: {sorted(_CAMPOS_PATCH_PERMITIDOS)}. El resto se "
                f"cambia por su método específico."
            )
        for nombre, valor in patch.items():
            setattr(self, nombre, valor)

    # ------------------------------------------------------------------
    # Representación (Unity)
    # ------------------------------------------------------------------

    def representar(self) -> dict:
        """
        Estado simulado de la celda para Unity, en unidades SI (K, Pa, m/s,
        kg/m³, W/m²). Los vectores van como {"x","y"}, el mismo formato que
        la casilla del Suelo. No incluye cachés ni campos internos.
        """
        return {
            "radiacion": self.radiacion,
            "temperatura_aire": self.temperatura.valor,  # aire, K
            "temperatura_suelo": self.temperatura.valor_suelo,  # K
            "presion": self.presion.valor,  # Pa
            "viento": {
                "intensidad": self.viento.intensidad,  # m/s
                "direccion": {
                    "x": self.viento.direccion.x,
                    "y": self.viento.direccion.y,
                },
            },
            "humedad_absoluta": self.humedad_absoluta.valor,  # kg/m³
            "humedad_relativa": self.humedad_relativa.valor,  # % (0-100)
        }
