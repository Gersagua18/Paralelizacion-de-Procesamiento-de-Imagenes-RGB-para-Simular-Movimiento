import numpy as np
import cv2
import queue
import threading

def leer_matrizImagen(imagen):
    resultado=[]
    with open(f"{imagen}","r") as matriz:
        for linea in matriz:
            fila=[]
            bloques=linea.strip("[],\n").split("], ")
            for bloque in bloques:
                valores=list(map(int,bloque.strip("[]").split(", ")))
                fila.append(valores)
            resultado.append(fila)
    return np.array(resultado, dtype=np.uint8)

def rotar_anillo(matriz,centro,tamaño_pixel=6,bloques_centro=1,pixeles_rotar=1,angulo=0,sentido='horario'):
    centro_x,centro_y=centro
    tmñ_centro=(bloques_centro * tamaño_pixel) // 2
    superior_x=centro_x-tmñ_centro
    superior_y=centro_y-tmñ_centro

    imagen_rotar=matriz.copy()

    for anillo in range(1,pixeles_rotar+1):
        bloque_anillo=[]
        for i in range(-anillo,bloques_centro+anillo):
            dx=superior_x+i*tamaño_pixel
            dy=superior_y-anillo*tamaño_pixel
            bloque_anillo.append((dx,dy))
        for i in range(0,bloques_centro+2*anillo-1):
            dx=superior_x+(bloques_centro+anillo-1)*tamaño_pixel
            dy=superior_y+(i-anillo+1)*tamaño_pixel
            bloque_anillo.append((dx,dy))
        for i in range(bloques_centro+anillo-1,-anillo-1,-1):
            dx=superior_x+i*tamaño_pixel
            dy=superior_y+(bloques_centro+anillo-1)*tamaño_pixel
            bloque_anillo.append((dx,dy))
        for i in range(bloques_centro+anillo-2,-anillo,-1):
            dx=superior_x-anillo*tamaño_pixel
            dy=superior_y+i*tamaño_pixel
            bloque_anillo.append((dx,dy))
        bloque=[]
        for (x,y) in bloque_anillo:
            mini_bloque=matriz[y:y+tamaño_pixel,x:x+tamaño_pixel]
            copia=mini_bloque.copy()
            bloque.append(copia)

        sentido_rotacion=int((angulo/360)*len(bloque))%len(bloque)
        if sentido == 'horario':
            bloque = bloque[-sentido_rotacion:] + bloque[:-sentido_rotacion]
        else:
            bloque = bloque[sentido_rotacion:] + bloque[:sentido_rotacion]

        for (x, y),block in zip(bloque_anillo, bloque):
            if 0<=x<matriz.shape[1]-tamaño_pixel and 0<=y<matriz.shape[0]-tamaño_pixel:
                imagen_rotar[y:y+tamaño_pixel,x:x+tamaño_pixel]=block
    return imagen_rotar

def avanzar_kernel(fondo_compartido, kernel, paso, fila, columna, multiplicador, cola, lock, angulo_rueda=None, ruedas=[]):
    kernel_ach=kernel.shape[1]
    kernel_alt=kernel.shape[0]

    with lock:
        for i in range(kernel_alt):
            for j in range(kernel_ach):
                if not np.all(kernel[i][j]==[255, 255, 255]):
                    fondo_compartido[i+fila][j+paso*multiplicador+columna]=kernel[i][j]

        for base, sentido in ruedas:
            centro_x_base,centro_y=base
            centro_x=centro_x_base+paso*multiplicador
            centro=(centro_x,centro_y)
            fondo_rotado=rotar_anillo(fondo_compartido, centro=centro, tamaño_pixel=2, bloques_centro=5, pixeles_rotar=3, angulo=angulo_rueda, sentido=sentido)
            fondo_compartido[:,:,:]=fondo_rotado

    cola.wait()

def mostrar_imagen(result_queue):
    cv2.namedWindow("Imagen RGB", cv2.WINDOW_NORMAL)
    while True:
        if not result_queue.empty():
            fond = result_queue.get()
            if fond is None:
                break
            cv2.imshow("Imagen RGB", fond)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    cv2.destroyAllWindows()

def avance():
    fondo=leer_matrizImagen("fondo.txt")
    carro1=leer_matrizImagen("carro1_mod.txt")
    carro2=leer_matrizImagen("carro2_mod.txt")

    pasos=30
    fila1=428
    fila2=500
    columna1=0
    columna2=fondo.shape[1]-250
    multiplicador1=30
    multiplicador2=-20
    result_queue=queue.Queue()
    lock=threading.Lock()
    cola=threading.Barrier(3)

    hilo_imprimir=threading.Thread(target=mostrar_imagen,args=(result_queue,))
    hilo_imprimir.start()

    ruedas_carro1=[(50, 503), (215, 503)]
    ruedas_carro2=[(1086, 576), (1250, 576)]

    sentidos1=['horario','horario']
    sentidos2=['antihorario','antihorario']
    angle=0
    for paso in range(pasos):
        fondo_compartido=fondo.copy()

        ruedas_c1=list(zip(ruedas_carro1,sentidos1))
        ruedas_c2=list(zip(ruedas_carro2,sentidos2))

        hilo_c1=threading.Thread(target=avanzar_kernel,
                                   args=(fondo_compartido, carro1, (1 + paso), fila1, columna1, multiplicador1,
                                         cola, lock, angle, ruedas_c1))

        hilo_c2=threading.Thread(target=avanzar_kernel,
                                   args=(fondo_compartido, carro2, (5 + paso), fila2, columna2, multiplicador2,
                                         cola, lock, angle, ruedas_c2))
        hilo_c1.start()
        hilo_c2.start()
        cola.wait()
        result_queue.put(fondo_compartido)
        hilo_c1.join()
        hilo_c2.join()
        angle = (angle + 10) % 360
    result_queue.put(None)
    hilo_imprimir.join()

if __name__ == "__main__":
    avance()