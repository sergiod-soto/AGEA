import numpy as np
from PIL import Image

def cargar_png(ruta):
    # Abrimos la imagen y la convertimos a escala de grises
    img = Image.open(ruta).convert("L")  # "L" = 0..255
    
    # Convertimos a array numpy (alto × ancho)
    return np.array(img, dtype=np.uint8)

   

