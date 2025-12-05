import numpy as np

#
#
#
#########################################################################
ancho = 200  # ANCHO DEL MAPA, INDEPENDIENTE DE LA RESOLUCION
alto = 200  # ALTO  "   "     "             "  "  "
#########################################################################
#
#
#

# mapa de suelo
mapa_suelo = np.zeros((alto, ancho), dtype=np.uint8)  # 0–255

# mapa de bioma
mapa_entidades = np.zeros((alto, ancho), dtype=np.uint8)  # 0–255








def guardar():
    np.savez("map_data.npz", suelo=mapa_suelo, entidades=mapa_entidades)