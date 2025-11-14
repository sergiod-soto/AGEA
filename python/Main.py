import multiprocessing
import os
import time
import csv
import csv
import time
import Conexion.Conexion as conexion
import Mundo.Datos as Datos
import time
import multiprocessing
import Funcionalidades.Sistema.Funciones_CSV as Funciones_CSV
from colorama import Fore, Style, init
from DEV.Funcionalidades import Cronometro
from DEV.Serie_Estados import Serie_Estados
from Mundo.Generacion.Generacion import Generacion
from Mundo.Generacion.Noise import Noise


init()  # inicializa colorama (necesario en Windows)

##################################################################
##################################################################


ancho, alto = 100, 100

#
# nomre del fichero que contiene las URLs de los demas ficheros
nombre_fichero_urls = "Urls.csv"
#
rutas_ficheros = {}
#
#


contadorBots = 0


#
#   mapas y diccionarios de cosas
#
mapa = [[None for _ in range(alto)] for _ in range(ancho)]
familias = {}
bots = {}
piedras = {}
comidas = {}
arboles = {}
aguas = {}
#
#
#

ancho = ancho
alto = alto
#
#
#


ruta_script = os.path.dirname(os.path.abspath(__file__))
ruta_archivo = os.path.join(ruta_script, nombre_fichero_urls)
rutas_ficheros = Funciones_CSV.leer_csv(ruta_archivo, ("ALIAS", "DIRECCION"))


#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
################################################################################
################################################################################
################################################################################
#
#
#


def set_estados():
    """creo la maquina de estados, los estados y seteo cada uno"""

    SE = Serie_Estados()

    contador = 0
    acciones = []

    # crear X bots basicos y ponerlos en cuadrado
    # region
    if True:
        for i in range(2):
            for j in range(2):
                bot_id = "b" + str(contador) + ".test"
                adn = [0]
                x = 15 * i
                y = 15 * j

                # congelamos bot_id y adn en el lambda mediante parámetros por defecto
                acciones.append(
                    lambda bot_id=bot_id, adn=adn: SE.Crear_Bot_Basico(bot_id, adn)
                )

                # movemos consultando Mundo.bots en el momento de ejecución; congelamos bot_id, x, y
                acciones.append(
                    lambda bot_id=bot_id, x=x, y=y: SE.Mover_Elemento(
                        Datos.bots[bot_id], (x, y)
                    )
                )

                contador += 1

        SE.add(acciones)
    # endregion

    return SE


def actualizar_shared_data(shared_data):
    """actualizo la variable compartida "shared_data" """

    shared_data["bots_data"] = manager.list(Datos.serializar_bots())
    shared_data["dev"] = manager.dict()


def main_loop(shared_data):
    """loop principal"""

    while True:
        # leer el estado de pausa desde el diccionario compartido
        if shared_data["other"]["paused"] == False:
            server_tic(shared_data)
        else:
            # evitar usar 100% CPU cuando está en pausa
            print("EN PAUSA...")
            time.sleep(0.1)


def server_tic(shared_data):
    """ejecuta un tic del servidor"""

    cronometro = Cronometro()
    cronometro.start_cronometro()

    actualizar_shared_data(shared_data)
    SE.do()

    tiempo = cronometro.stop_cronometro()
    # print("\n\nEste tic del server ha tardado: " + str(tiempo) + "s\n\n")

    time.sleep(shared_data["other"]["1/fps/1000"] / 1000)


#
#
#
################################################################################
################################################################################
################################################################################
#
#
#
if __name__ == "__main__":

    # inicializamos y seteamos la serie de estados:
    SE = set_estados()

    # creamos el manager para tener una variable
    # compartida entre procesos
    manager = multiprocessing.Manager()
    shared_data = manager.dict()

    shared_data["bots_data"] = manager.list()  # datos de los bots
    shared_data["other"] = manager.dict()  # otras cosas
    shared_data["dev"] = manager.dict()  # reservado para testeo
    shared_data["other"]["1/fps/1000"] = 500  # ms por fotograma
    shared_data["other"]["paused"] = False  # esta en pausa

    # Arranca la conexion en un proceso aparte
    # p = multiprocessing.Process(target=conexion.run_exporter, args=(shared_data,))
    # p.start()

    print("creando mapa:")
    crono = Cronometro()
    crono.start_cronometro()

    generator = Generacion(
        x=1500, y=1500, seeds={"base": 1, "desiertos_y_tundras": 2, "mar_y_selvas": 3}
    )

    print("ha tardado en generarse el ruido: " + str(crono.stop_cronometro()) + "s")

    # Bucle principal
    # main_loop(shared_data)
