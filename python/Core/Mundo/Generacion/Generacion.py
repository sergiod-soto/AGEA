from Core.Mundo.Generacion.noise import Noise
import exceptions
from pathlib import Path

""" 

script para la generacion aleatoria del mundo.
incluye cosas como las masas de agua, las montañas, rocas, biomas, etc, pero no loos bots

"""


class Generacion:

    def __init__(self, x, y, seeds):
        self.direccion_base = str(Path.cwd() / "Mundo" / "Mascaras")
        self.noise_base = Noise(seeds["base"])
        self.seeds = seeds
        self.width = x
        self.heigh = y

        # setings de los parametros iniciales del Noise base
        self.noise_base = self.noise_base.with_params(
            scale=300, octaves=1, persistence=0.3, lacunarity=2.0
        )
        # cargar mascaras
        self.cargar_mascaras(
            "",
            [
                "desiertos.png",
                "bosques.png",
                "praderas.png",
                "selvas.png",
                "tundras.png",
                "montanhas.png",
                "oasis.png",
                "bosques.png",
                "mares.png",
            ],
        )

    def cargar_mascaras(self, direccion, mascaras):

        def _load(self, ruta):
            try:
                return self.noise_base.load(direccion + ruta)
            except exceptions.NoMaskFound as e:
                print(f"\033[31m\tNo encontrada mascara: [{direccion} {ruta}]\033[0m")
                raise e

        todas_mascaras_cargadas = True
        for ruta in mascaras:
            nombre = ruta.split(".")[0]  # Quita la extensión (.png)
            try:
                ruta = "\\" + ruta
                setattr(self, nombre, _load(self, ruta))
            except exceptions.NoMaskFound:
                todas_mascaras_cargadas = False

        if todas_mascaras_cargadas == False:
            self.generar_mascaras()

    def generar_mascaras(self):

        #  ------------- CAPAS BIOMA -------------

        #        DESIERTOS Y TUNDRAS  ------------
        #
        #  creacion de la mascara BASE de desiertos y tundras
        self.desiertos_y_tundras = self.noise_base.Forma.manchas_irregulares(
            seed=self.seeds["desiertos_y_tundras"],
            num_manchas=5,
            distancia_min=0.2,
            radio_medio=0.1,
            variacion_radio=0.2,
        )

        #  creacion de la mascara de desiertos
        self.desiertos = self.desiertos_y_tundras.Funcion.manchas_blancas_a_blancas(
            self.desiertos_y_tundras
        )

        #  creacion de la mascara de tundras
        self.tundras = self.desiertos_y_tundras.Funcion.manchas_negras_a_blancas(
            self.desiertos_y_tundras
        )
        #

        #        SABANAS Y TAIGAS     ------------
        #  creacion de la mascara de sabana
        self.sabanas = self.desiertos_y_tundras.Forma.halo_alrededor(
            self.desiertos_y_tundras, target_color=1.0
        )
        self.sabanas = self.desiertos_y_tundras.Forma.recortar_halo(
            self.desiertos_y_tundras, self.sabanas
        )

        #  creacion de la mascara de taiga
        self.taiga = self.desiertos_y_tundras.Forma.halo_alrededor(
            self.desiertos_y_tundras, target_color=0.0
        )
        self.taiga = self.desiertos_y_tundras.Forma.recortar_halo(
            self.desiertos_y_tundras, self.taiga
        )
        #

        #        SELVAS Y MARES       ------------
        #  creacion de la mascara BASE de selvas y mares
        self.mar_y_selvas = self.noise_base.Forma.manchas_blancas_y_negras(
            num_manchas=5, variacion_borde=0.4, seed=self.seeds["mar_y_selvas"]
        )

        #  creacion de la mascara de selva
        self.selva = self.mar_y_selvas.Funcion.manchas_negras_a_blancas(
            self.mar_y_selvas
        )

        #  creacion de la mascara de mar
        self.mar = self.mar_y_selvas.Funcion.manchas_blancas_a_blancas(
            self.mar_y_selvas
        )
        #

        #        BOSQUES Y COSTAS     ------------
        #  creacion de la mascara de bosque
        self.bosque = self.selva.Forma.halo_alrededor(self.selva, target_color=1.0)
        self.bosque = self.bosque.Forma.recortar_halo(self.mar_y_selvas, self.bosque)

        #  creacion de la mascara de costa
        self.costa = self.mar.Forma.halo_alrededor(self.mar, target_color=1.0)
        self.costa = self.costa.Forma.recortar_halo(self.mar_y_selvas, self.costa)
        #
        #

    #  ------------- CAPAS CLIMA -------------

    #  HUMEDAD
    # TODO
    def generar_humedad(self):
        raise NotImplementedError("No implementado")

    #  TEMPERATURA
    def generar_temperatura(self):
        base = Noise(seed=2562)

        noise = base.with_params(scale=10.0, octaves=4, persistence=0.6, lacunarity=1.0)

        noise_n_s = noise.gradiente_norte_sur()
        noise_min = noise_n_s.sumar(-0.1)
        noise_max = noise_n_s.sumar(0.1)
        noise = noise.modulado_por_gradiente(noise_n_s)
        noise = noise.combinar(noise_n_s, 1.0)
        noise = noise.minimo_con(noise_min)
        noise = noise.maximo_con(noise_max)

        noise.show(100, 100)

        return noise

    #  ------------- CAPAS BIOMA -------------
    def get_mascara_praderas(self):
        raise NotImplementedError("No implementado")

    def get_mascara_tundras(self):
        return self.tundras

    def get_mascara_desiertos(self):
        return self.desiertos

    def get_mascara_selvas(self):
        return self.selva

    def get_mascara_bosques(self):
        return self.bosque

    def get_mascara_sabanas(self):
        return self.sabanas

    def get_mascara_taigas(self):
        return self.taiga

    def get_mascara_costas(self):
        return self.costa

    def get_mascara_mares(self):
        return self.mar

    # endregion

    def dev(self):
        pass
