from concurrent.futures import ThreadPoolExecutor
from opensimplex import OpenSimplex
import numpy as np
from PIL import Image
from opensimplex import OpenSimplex
import math
import random
import Exceptions
import hashlib


class Noise:

    def __init__(self, seed=None, func=None):
        self.seed = seed
        if func is not None:
            # Noise "derivado" (por combinación, gradiente, etc.)
            self.func = func
            self.noise = None
        else:
            # Noise base (ruido simplex)
            self.noise = OpenSimplex(seed)
            self.func = None

        # Parámetros por defecto
        self.scale = 1.0
        self.octaves = 1
        self.persistence = 0.5
        self.lacunarity = 2.0

        # Instancias auxiliares
        self.Forma = self._Forma(self)
        self.Funcion = self._Funcion(self)

    # def _serializar(self):
    #     serializado = str(self.seed) + ", " + str(self.func.__qualname__)
    #     return serializado
    


    def __call__(
        self, x, y, scale=None, octaves=None, persistence=None, lacunarity=None
    ):
        # Usa los parámetros actuales del objeto si no se pasan explícitos
        scale = scale or self.scale
        octaves = octaves or self.octaves
        persistence = persistence or self.persistence
        lacunarity = lacunarity or self.lacunarity

        if self.func is not None:
            return np.clip(self.func(x, y), 0.0, 1.0)
        else:
            amp = 1.0
            freq = scale
            total = 0.0
            maxamp = 0.0
            for _ in range(octaves):
                total += self.noise.noise2(x * freq, y * freq) * amp
                maxamp += amp
                amp *= persistence
                freq *= lacunarity
            return (total / maxamp + 1) / 2

    # --- Nuevo método para configurar parámetros ---
    def with_params(self, scale=None, octaves=None, persistence=None, lacunarity=None):
        """
        Devuelve un nuevo Noise con los mismos datos pero parámetros de ruido modificados.
        """
        new_noise = Noise(self.seed, self.func)
        new_noise.scale = scale if scale is not None else self.scale
        new_noise.octaves = octaves if octaves is not None else self.octaves
        new_noise.persistence = (
            persistence if persistence is not None else self.persistence
        )
        new_noise.lacunarity = lacunarity if lacunarity is not None else self.lacunarity
        return new_noise

    @staticmethod
    def load(path):
        """
        Carga una imagen (PNG, JPG, etc.) y devuelve un Noise(func=func)
        que devuelve valores normalizados [0,1].
        """
        try:
            img = Image.open(path).convert("L")  # Escala de grises
        except Exception as e:
            raise Exceptions.NoMaskFound(e)

        ancho, alto = img.size
        pix = np.array(img, dtype=np.float32) / 255.0

        def func(x, y):
            # Limitar el rango [0,1]
            x = max(0, min(1, x))
            y = max(0, min(1, y))

            # Coordenadas reales dentro de la imagen
            fx = x * (ancho - 1)
            fy = y * (alto - 1)

            # Interpolación bilineal suave
            x0, y0 = int(fx), int(fy)
            x1, y1 = min(x0 + 1, ancho - 1), min(y0 + 1, alto - 1)
            dx, dy = fx - x0, fy - y0

            v00 = pix[y0, x0]
            v10 = pix[y0, x1]
            v01 = pix[y1, x0]
            v11 = pix[y1, x1]

            return (
                v00 * (1 - dx) * (1 - dy)
                + v10 * dx * (1 - dy)
                + v01 * (1 - dx) * dy
                + v11 * dx * dy
            )

        return Noise(func=func)

    class _Forma:

        def __init__(self, parent):
            self.parent = parent

        def gradiente_norte_sur(self, height=1.0, invert=False):
            """
            Devuelve un nuevo Noise que representa un gradiente norte-sur.
            y=0 -> 0, y=height -> 1 (o al revés si invert=True)
            """

            def grad_func(x, y):
                val = y / height
                if invert:
                    val = 1 - val
                return np.clip(val, 0.0, 1.0)

            return Noise(func=grad_func)

        def gradiente_este_oeste(self, width=1.0, invert=False):
            """
            Devuelve un nuevo Noise que representa un gradiente este-oeste.
            x=0 -> 0, x=width -> 1 (o al revés si invert=True)
            """

            def grad_func(x, y):
                val = x / width
                if invert:
                    val = 1 - val
                return np.clip(val, 0.0, 1.0)

            return Noise(func=grad_func)

        def gradiente_diagonal_noreste_suroeste(
            self, width=1.0, height=1.0, invert=False
        ):

            def grad_func(x, y):
                val = (x / width + y / height) / 2.0
                if invert:
                    val = 1 - val
                return np.clip(val, 0.0, 1.0)

            return Noise(func=grad_func)

        def frontera_horizontal(self, height=1.0, limite=0.5, invert=False):

            def func(x, y):
                val = 1.0 if (y / height) >= limite else 0.0
                if invert:
                    val = 1.0 - val
                return val

            return Noise(func=func)

        def frontera_vertical(self, width=1.0, limite=0.5, invert=False):

            def func(x, y):
                val = 1.0 if (x / width) >= limite else 0.0
                if invert:
                    val = 1.0 - val
                return val

            return Noise(func=func)

        def frontera_diagonal(self, width=1.0, height=1.0, invert=False):

            def func(x, y):
                val = 1.0 if (x / width) + (y / height) >= 1.0 else 0.0
                if invert:
                    val = 1.0 - val
                return val

            return Noise(func=func)

        def frontera_central_rectangular(
            self,
            width=1.0,
            height=1.0,
            rect_centro=(0.5, 0.5),
            rect_tamano=(0.3, 0.3),
            invert=False,
        ):
            cx, cy = rect_centro
            rw, rh = rect_tamano

            x_min = (cx - rw / 2) * width
            x_max = (cx + rw / 2) * width
            y_min = (cy - rh / 2) * height
            y_max = (cy + rh / 2) * height

            def func(x, y):
                val = 1.0 if (x_min <= x <= x_max and y_min <= y <= y_max) else 0.0
                if invert:
                    val = 1.0 - val
                return val

            return Noise(func=func)

        def manchas_aisladas(
            self,
            num_manchas=100,
            radio_medio=0.05,
            variacion_radio=0.5,
            gris_base=0.5,
            distancia_min=0.02,
        ):
            """
            Genera un Noise con fondo gris_base y manchas blancas/negras aisladas, sin solaparse
            y con una distancia mínima entre ellas.

            Parámetros:
            - num_manchas: cantidad total de manchas
            - radio_medio: radio medio relativo (0.05 = 5% del ancho total)
            - variacion_radio: variación aleatoria del radio
            - gris_base: valor del fondo
            - distancia_min: distancia mínima entre manchas (centro a centro, en coordenadas normalizadas)
            """

            manchas = []

            for _ in range(num_manchas):
                r = radio_medio * random.uniform(
                    1 - variacion_radio, 1 + variacion_radio
                )
                color = 1.0 if random.random() < 0.5 else 0.0

                for intento in range(300):  # más intentos para asegurar separación
                    x = random.uniform(r, 1 - r)
                    y = random.uniform(r, 1 - r)

                    # comprobar que no se superpone ni viola la distancia mínima
                    if all(
                        math.hypot(x - ox, y - oy) >= (r + orad + distancia_min)
                        for ox, oy, orad, _ in manchas
                    ):
                        manchas.append((x, y, r, color))
                        break

            def func(x, y):
                val = gris_base
                for cx, cy, r, color in manchas:
                    if (x - cx) ** 2 + (y - cy) ** 2 <= r**2:
                        val = color
                        break
                return val

            return Noise(func=func)

        def manchas_irregulares(
            self,
            seed=0,
            num_manchas=100,
            radio_medio=0.05,
            variacion_radio=0.5,
            gris_base=0.5,
            distancia_min=0.02,
            irregularidad=0.3,
            detalles=8,
        ):
            """
            Genera un Noise determinista con fondo gris_base y manchas irregulares blancas/negras.
            Las manchas no se superponen ni se acercan demasiado, y tienen bordes no circulares.

            Parámetros:
            - seed: semilla determinista
            - num_manchas: número total de manchas
            - radio_medio: radio medio relativo (0.05 = 5% del ancho total)
            - variacion_radio: variación aleatoria del radio de cada mancha
            - gris_base: valor base del fondo
            - distancia_min: distancia mínima entre manchas (en coordenadas normalizadas)
            - irregularidad: cuánto varía el radio a lo largo del contorno (0 = círculo perfecto)
            - detalles: número de “picos” o segmentos que definen la irregularidad
            """

            rng = random.Random(seed)  # generador determinista
            manchas = []

            # Preparar las manchas con forma irregular
            for _ in range(num_manchas):
                r_base = radio_medio * rng.uniform(
                    1 - variacion_radio, 1 + variacion_radio
                )
                color = 1.0 if rng.random() < 0.5 else 0.0

                # Intentar colocar sin solaparse ni violar distancia mínima
                for intento in range(300):
                    x = rng.uniform(r_base, 1 - r_base)
                    y = rng.uniform(r_base, 1 - r_base)

                    if all(
                        math.hypot(x - ox, y - oy) >= (r_base + orad + distancia_min)
                        for ox, oy, orad, *rest in manchas
                    ):
                        break
                else:
                    continue  # no se pudo colocar, saltar esta mancha

                # Crear contorno irregular
                contorno = []
                for i in range(detalles):
                    ruido = math.sin(i * rng.uniform(0.5, 2.0) + rng.random() * math.pi)
                    r = r_base * (
                        1 + rng.uniform(-irregularidad, irregularidad) * abs(ruido)
                    )
                    ang = (2 * math.pi / detalles) * i
                    contorno.append((ang, r))

                manchas.append((x, y, r_base, color, contorno))

            # Función evaluable del noise
            def func(x, y):
                val = gris_base
                for cx, cy, r_base, color, contorno in manchas:
                    dx = x - cx
                    dy = y - cy
                    dist = math.hypot(dx, dy)
                    ang = math.atan2(dy, dx)
                    if ang < 0:
                        ang += 2 * math.pi

                    # Interpolar radio máximo permitido según ángulo
                    i = int((ang / (2 * math.pi)) * len(contorno))
                    i2 = (i + 1) % len(contorno)
                    t = ((ang / (2 * math.pi)) * len(contorno)) - i
                    r_lim = contorno[i][1] * (1 - t) + contorno[i2][1] * t

                    if dist <= r_lim:
                        val = color
                        break
                return val

            return Noise(func=func)

        def halo_alrededor(self, base_noise, target_color=1.0, radio_halo=0.05):
            """
            Devuelve un Noise negro con halos blancos alrededor de las manchas de color `target_color`

            Parámetros:
            - base_noise: Noise original con manchas blancas y negras
            - target_color: color de las manchas a rodear (1.0 = blanco, 0.0 = negro)
            - radio_halo: radio del halo en coordenadas normalizadas (0-1)
            """

            def func(x, y):
                val = 0.0  # fondo negro
                # recorrer la vecindad para detectar si hay target_color cerca
                # aquí usamos una aproximación: sampleamos varios puntos alrededor
                pasos = 8  # número de muestras alrededor
                for dx in [-radio_halo, 0, radio_halo]:
                    for dy in [-radio_halo, 0, radio_halo]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx <= 1 and 0 <= ny <= 1:
                            if base_noise(nx, ny) == target_color:
                                val = 1.0
                                return val
                return val

            return Noise(func=func)

        def recortar_halo(self, base_manchas, halo_noise, gris_base=0.5):
            """
            Devuelve un Noise donde el halo no cubre las manchas existentes
            (blancas o negras) del noise base.

            Parámetros:
            - base_manchas: Noise original con manchas blancas y negras
            - halo_noise: Noise con halos que queremos recortar
            - gris_base: valor que se considera “fondo” en base_manchas (si es 0.5, por ejemplo)
            """

            def func(x, y):
                # Si hay mancha en el noise base (distinta del gris_base), ponemos negro
                if base_manchas(x, y) != gris_base:
                    return 0.0
                # En caso contrario, devolvemos el valor original del halo
                return halo_noise(x, y)

            return Noise(func=func)

        def manchas_blancas_y_negras(
            self,
            num_manchas=5,
            distancia_min=0.1,
            num_nodos=(6, 12),
            radio=(0.05, 0.15),
            variacion_borde=0.4,
            seed=None,
        ):
            """
            Retorna un Noise con manchas blancas y negras sobre fondo gris (0.5),
            con formas suaves y bordes redondeados tipo "lagos".

            Parámetros:
            - num_manchas: número total de manchas.
            - distancia_min: distancia mínima entre centros de manchas.
            - num_nodos: rango de nodos que define la complejidad del polígono.
            - radio: rango de radios base de las manchas.
            - variacion_borde: cuánto puede variar la distancia de cada nodo al centro.
            - seed: semilla para reproducibilidad.
            """

            if seed is not None:
                random.seed(seed)

            manchas = []  # [(cx, cy, puntos, color, r)]

            # --- Catmull-Rom Spline para suavizar contorno ---
            def catmull_rom_spline(puntos, n_puntos=10):
                puntos = puntos + puntos[:3]  # cerrar el loop
                salida = []
                for i in range(len(puntos) - 3):
                    p0, p1, p2, p3 = (
                        puntos[i],
                        puntos[i + 1],
                        puntos[i + 2],
                        puntos[i + 3],
                    )
                    for t in np.linspace(0, 1, n_puntos):
                        t2 = t * t
                        t3 = t2 * t
                        x = 0.5 * (
                            (2 * p1[0])
                            + (-p0[0] + p2[0]) * t
                            + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                            + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
                        )
                        y = 0.5 * (
                            (2 * p1[1])
                            + (-p0[1] + p2[1]) * t
                            + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                            + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
                        )
                        salida.append((x, y))
                return salida

            # --- Generar polígono irregular ---
            def generar_poligono_irregular(cx, cy, r_base, nodos):
                puntos = []
                for _ in range(nodos):
                    ang = random.uniform(0, 2 * math.pi)
                    dist = (
                        r_base
                        * random.uniform(0.6, 1.0)
                        * (1 + variacion_borde * random.uniform(-1, 1))
                    )
                    x = cx + math.cos(ang) * dist
                    y = cy + math.sin(ang) * dist
                    puntos.append((x, y))
                puntos.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
                return catmull_rom_spline(puntos, n_puntos=5)

            # --- Generar manchas ---
            intentos = 0
            while len(manchas) < num_manchas and intentos < num_manchas * 20:
                intentos += 1
                cx, cy = random.random(), random.random()
                r = random.uniform(*radio)
                if all(
                    math.hypot(cx - ox, cy - oy) >= (r + orad + distancia_min)
                    for ox, oy, _, _, orad in manchas
                ):
                    color = 1.0 if random.random() < 0.5 else 0.0
                    puntos = generar_poligono_irregular(
                        cx, cy, r, random.randint(*num_nodos)
                    )
                    manchas.append((cx, cy, puntos, color, r))

            # --- Función Noise ---
            def func(x, y):
                val = 0.5  # fondo gris
                for cx, cy, puntos, color, r in manchas:
                    inside = False
                    j = len(puntos) - 1
                    for i in range(len(puntos)):
                        xi, yi = puntos[i]
                        xj, yj = puntos[j]
                        if ((yi > y) != (yj > y)) and (
                            x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi
                        ):
                            inside = not inside
                        j = i
                    if inside:
                        val = color
                        break
                return val

            return Noise(func=func)

    class _Funcion:

        def __init__(self, outer):
            self.outer = outer

        def __call__(
            self, x, y, scale=None, octaves=None, persistence=None, lacunarity=None
        ):
            # Usa los parámetros actuales del objeto si no se pasan explícitos
            scale = scale or self.outer.scale
            octaves = octaves or self.outer.octaves
            persistence = persistence or self.outer.persistence
            lacunarity = lacunarity or self.outer.lacunarity

            if self.outer.func is not None:
                return np.clip(self.outer.func(x, y), 0.0, 1.0)
            else:
                amp = 1.0
                freq = scale
                total = 0.0
                maxamp = 0.0
                for _ in range(octaves):
                    total += self.outer.noise.noise2(x * freq, y * freq) * amp
                    maxamp += amp
                    amp *= persistence
                    freq *= lacunarity
                return (total / maxamp + 1) / 2

        def combinar(self, other, factor=1.0):
            """
            Devuelve un nuevo Noise que combina este con otro usando un factor.
            factor = 0    -> 100% self
            factor = 0.5  -> 50% self, 50% other
            factor = 1    -> 100% other
            """

            if factor < 0.0 or factor > 1.0:
                raise ValueError(
                    f"Valor de factor fuera del rango 0.0 - 1.0 ({factor})"
                )

            def combined_func(x, y):
                n1 = self.outer(x, y)
                n2 = other(x, y)
                return ((1 - factor) * n2) + (factor * n1)

            return Noise(func=combined_func)

        def minimo_con(self, other_noise):
            """Devuelve un nuevo Noise donde el valor en cada punto es al menos el del otro Noise."""

            def func(x, y):
                a = self.outer(x, y)
                b = other_noise(x, y)
                return np.maximum(a, b)

            return Noise(func=func)

        def maximo_con(self, other_noise):
            """Devuelve un nuevo Noise donde el valor en cada punto es como máximo el del otro Noise."""

            def func(x, y):
                a = self.outer(x, y)
                b = other_noise(x, y)
                return np.minimum(a, b)

            return Noise(func=func)

        def sumar(self, offset):

            def func(x, y):
                return np.clip(self.outer(x, y) + offset, 0.0, 1.0)

            return Noise(func=func)

        def modulado_por_gradiente(self, grad_noise):
            def func(x, y):
                g = grad_noise(x, y)
                r = self.outer(x, y)
                if isinstance(g, np.ndarray):  # para llamadas en batch
                    return np.where(g < 0.5, r * (g * 2), r + (1 - r) * ((g - 0.5) * 2))
                else:  # para llamada escalar
                    return r * (g * 2) if g < 0.5 else r + (1 - r) * ((g - 0.5) * 2)

            return Noise(func=func)

        def multiplicar(self, other):

            def func(x, y):
                return np.clip(self.outer(x, y) * other(x, y), 0.0, 1.0)

            return Noise(func=func)

        def difuminar_kernel(self, radio=0.02, pasos=3, tipo="gauss"):
            """
            Aplica un difuminado espacial al Noise usando un kernel 2D.

            Parámetros:
                radio: distancia máxima (en unidades de coordenadas) para muestrear vecinos
                pasos: número de divisiones por eje (3 → 3x3 muestras)
                tipo: 'gauss' o 'media' (define la ponderación)
            """
            import math

            # Precalcula offsets del kernel
            coords = np.linspace(-radio, radio, pasos)
            offsets = [(dx, dy) for dx in coords for dy in coords]

            # Si es gaussiano, calculamos pesos
            if tipo == "gauss":
                sigma = radio / 2
                pesos = [
                    math.exp(-(dx**2 + dy**2) / (2 * sigma**2)) for dx, dy in offsets
                ]
            else:
                pesos = [1.0 for _ in offsets]

            total_peso = sum(pesos)

            def func(x, y):
                val = 0.0
                for (dx, dy), w in zip(offsets, pesos):
                    val += self.outer(x + dx, y + dy) * w
                return np.clip(val / total_peso, 0.0, 1.0)

            return Noise(func=func)

        def manchas_negras_a_blancas(self, base_manchas):
            """
            Devuelve un Noise negro con las manchas negras (0.0) convertidas a blancas (1.0)
            y el resto negro.
            """

            def func(x, y):
                val = base_manchas(x, y)
                if val == 0.0:  # mancha negra
                    return 1.0
                return 0.0  # fondo o manchas blancas

            return Noise(func=func)

        def manchas_blancas_a_blancas(self, base_manchas):
            """
            Devuelve un Noise negro con las manchas blancas (1.0) conservadas como blancas
            y el resto negro.
            """

            def func(x, y):
                val = base_manchas(x, y)
                if val == 1.0:  # mancha blanca
                    return 1.0
                return 0.0  # fondo o manchas negras

            return Noise(func=func)

        def maskar_noises(noise1, noise2, threshold=0.95, in_place=False):
            """
            Pone de color negro en noise2 los puntos donde ambos Noise son blancos.

            Parámetros:
            - noise1, noise2: objetos Noise (función(x,y) -> valor entre 0 y 1)
            - threshold: valor mínimo que se considera "blanco"
            - in_place: si True, modifica noise2 directamente; si False, devuelve uno nuevo.
            """

            def func(x, y):
                v1 = noise1(x, y)
                v2 = noise2(x, y)
                if v1 >= threshold and v2 >= threshold:
                    return 0.0  # negro
                return v2  # mantiene el valor del segundo Noise

            if in_place:
                noise2.func = func
                return noise2
            else:
                return Noise(func=func)

    def show(
        self,
        ancho=100,
        alto=100,
        scale=5.0,
        octaves=4,
        persistence=0.5,
        lacunarity=2.0,
    ):
        datos = np.zeros((alto, ancho), dtype=np.float32)
        for y in range(alto):
            for x in range(ancho):
                nx = x / ancho
                ny = y / alto
                datos[y, x] = self(nx, ny, scale, octaves, persistence, lacunarity)

        datos = (datos * 255).astype(np.uint8)
        img = Image.fromarray(datos, mode="L")
        img.show()

        return img

    def save(self, path, size=(512, 512), threads=8):
        """
        Guarda este Noise como imagen en escala de grises (0–255),
        usando múltiples hilos para acelerar el cálculo.
        """
        if self.func is None:
            raise ValueError("No hay función de ruido (func) definida en este Noise.")

        w, h = size
        data = np.zeros((h, w), dtype=np.uint8)

        # Función interna que calcula una fila
        def procesar_fila(j):
            y = j / (h - 1)
            fila = np.zeros(w, dtype=np.uint8)
            for i in range(w):
                x = i / (w - 1)
                val = self.func(x, y)
                val = np.clip(val, 0.0, 1.0)
                fila[i] = int(val * 255)
            return j, fila

        # Ejecutar en paralelo
        with ThreadPoolExecutor(max_workers=threads) as executor:
            for j, fila in executor.map(procesar_fila, range(h)):
                data[j, :] = fila

        img = Image.fromarray(data, mode="L")
        img.save(path)
        print(f"✅ Noise guardado en '{path}' ({w}x{h})")

    def get_seed(self):
        return self.seed
