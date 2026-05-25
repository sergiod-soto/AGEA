import multiprocessing
import os
import time
import multiprocessing
import os
import signal


from Core.Mundo.Generacion.generacion import Generacion
from Dev.Testing import FakeClient
from Dev.Testing.Estados import set_estados
import Utils.Sistema.funciones_csv as funciones_csv
import Core.Mundo.datos as Datos
import Services.Conexion_Visualizador.conexion as Conexion

from Dev.Serie_Estados import Serie_Estados

from Core.Perfiles.logica import obtener_datos_perfiles

##################################################################
##################################################################


##################################################################
##################################################################
debug = False

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
rutas_ficheros = funciones_csv.leer_csv(ruta_archivo, ("ALIAS", "DIRECCION"))


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


def actualizar_shared_data(shared_data):
    """actualizo la variable compartida "shared_data" """

    shared_data["bots"].update(Datos.serializar_bots())

    # shared_data["dev"] = manager.dict()


def main_loop(shared_data):
    """loop principal"""

    try:
        while True:
            # leer el estado de pausa desde el diccionario compartido
            if shared_data["other"]["paused"] == False:
                server_tic(shared_data)
            else:
                # evitar usar 100% CPU cuando está en pausa
                print("EN PAUSA...")
                time.sleep(0.1)
    except:
        print("error en main loop")


def server_tic(shared_data):
    """Ejecuta un tic del servidor"""

    # actualizo datos compartidos
    actualizar_shared_data(shared_data)

    """Mando los datos al cliente"""

    # siguiente estado
    # SE.do()

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

running = True


def handler(signum, frame):
    global running
    running = False


if __name__ == "__main__":

    # inicializamos y seteamos la serie de estados:
    SE = set_estados()

    # creamos el manager para tener una variable
    # compartida entre procesos
    manager = multiprocessing.Manager()
    shared_data = manager.dict()

    shared_data["bots"] = manager.dict()  # datos de los bots
    shared_data["mundo"] = None  # el mundo
    shared_data["other"] = manager.dict()  # otras cosas
    shared_data["dev"] = manager.dict()  # reservado para testeo
    shared_data["other"]["1/fps/1000"] = 500  # ms por fotograma
    shared_data["other"]["paused"] = False  # esta en pausa
    shared_data["other"]["conn_ready"] = False

    # cola para comunicación de mensajes hacia el exportador

    # Arranca la conexion en un proceso aparte
    proceso_exporter = Conexion.thread_exporter(shared_data)

    time.sleep(1)

    if debug:
        FakeClient.start_fake_client()
        FakeClient.run_demo()

    

    while running:
        # Bucle principal
        main_loop(shared_data)

    print("Python finalizado limpiamente")
