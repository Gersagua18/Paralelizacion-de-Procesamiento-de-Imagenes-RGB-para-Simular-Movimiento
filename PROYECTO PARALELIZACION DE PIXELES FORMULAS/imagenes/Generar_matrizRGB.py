from PIL import Image
import numpy as np

def image_to_matrix(ruta, resolution):
    imagen=Image.open(ruta)
    reforma_imagen=imagen.resize(resolution)
    imagen_rgb=reforma_imagen.convert("RGB")
    matriz= np.array(imagen_rgb)

    matriz = matriz.tolist()
    return matriz

ruta="imagenes/carro1.jpg"
resolution=(270,100)

imagen_matriz=image_to_matrix(ruta, resolution)

with open("carro1.txt", "w") as file:
    for row in imagen_matriz:
        file.write(f"{row},\n")

print("La matriz de píxeles se ha guardado.")
    
