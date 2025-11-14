import matplotlib.pyplot as plt
import threading



def generar_grafico_lineas(datos, titulo_grafico, titulo_x, titulo_y):

    def mostrar_grafico():
        x = [p[0] for p in datos]
        y = [p[1] for p in datos]
        plt.figure("Gráfico de líneas")
        plt.plot(x, y)
        plt.title(titulo_grafico)
        plt.xlabel(titulo_x)
        plt.ylabel(titulo_y)
        plt.grid(True)
        plt.show()

    # Ejecutamos el gráfico en un hilo separado para no bloquear Pygame
    threading.Thread(target=mostrar_grafico).start()


def generar_grafico_histograma(datos, titulo_grafico, titulo_x, titulo_y):

    def mostrar_histograma():
        plt.figure("Histograma")
        plt.hist(datos, bins=10, edgecolor='black', color='skyblue')
        plt.title(titulo_grafico)
        plt.xlabel(titulo_x)
        plt.ylabel(titulo_y)
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    threading.Thread(target=mostrar_histograma).start()


def generar_grafico_barras(etiquetas, valores, titulo_grafico, titulo_x, titulo_y):

    def mostrar_barras():
        plt.figure("Gráfico de Barras")
        plt.bar(etiquetas, valores, color='skyblue', edgecolor='black')
        plt.title(titulo_grafico)
        plt.xlabel(titulo_x)
        plt.ylabel(titulo_y)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.grid(axis='y')
        plt.show()

    threading.Thread(target=mostrar_barras).start()
