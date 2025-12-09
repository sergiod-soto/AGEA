from Core.Mundo import Datos
from Dev.Serie_Estados import Serie_Estados

SE = Serie_Estados()


def set_estados():
    """creo la maquina de estados, los estados y seteo cada uno"""

    contador = 0
    acciones = []

    # crear X bots basicos y ponerlos en cuadrado
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

    # recursivamente rota un bot
    #SE.add([lambda: SE.test()])

    return SE
