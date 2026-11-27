"""
Procesador de operaciones del dominio, semana 13 (pasos 2 y 3).

Consume la cola durable 'operaciones'. Es una réplica SIN estado, se puede
escalar con --scale procesador=3 y cada mensaje lo recibe una sola réplica
(competing consumers).

En el laboratorio el procesamiento se simula con una espera (DEMORA). En el
trabajo autónomo esta función llama al servidor real del proyecto.

Variables
  AUTO_ACK  0 | 1   con 0, ack manual al TERMINAR (at-least-once)
                    con 1, el broker lo da por entregado al SALIR (at-most-once)
  DEMORA    (3)     segundos que tarda en "procesar" cada operación
"""
import json
import os
import time

from cola import COLA_OPERACIONES, conectar, declarar, log

AUTO_ACK = os.environ.get("AUTO_ACK", "0") == "1"
DEMORA = float(os.environ.get("DEMORA", "3"))

# Operaciones del servicio de juegos (las mismas de dominio.py y objetos.py).
OPERACIONES_VALIDAS = {"TABLA", "UNIR", "ANOTAR"}


def procesar(mensaje):
    """Simula el trabajo. Aquí iría la llamada al servidor del proyecto."""
    time.sleep(DEMORA)
    return f"{mensaje['op']} {' '.join(mensaje['args'])} procesada"


def al_recibir(canal, metodo, props, cuerpo):
    mensaje = json.loads(cuerpo)
    marca = " (REENTREGADO)" if metodo.redelivered else ""
    log(f"recibido id={mensaje['id']} op={mensaje['op']}{marca}")

    if mensaje["op"] not in OPERACIONES_VALIDAS:
        # Mensaje venenoso. Si lo devolviéramos a la cola volvería a fallar
        # para siempre, por eso se descarta sin reintentar (requeue=False).
        log(f"descartado id={mensaje['id']}, operación desconocida {mensaje['op']}")
        if not AUTO_ACK:
            canal.basic_reject(delivery_tag=metodo.delivery_tag, requeue=False)
        return

    log(f"procesando id={mensaje['id']} ...")
    resultado = procesar(mensaje)
    if not AUTO_ACK:
        # Recién aquí el broker borra el mensaje. Si la réplica muere antes
        # de esta línea, el broker lo reentrega a otra.
        canal.basic_ack(delivery_tag=metodo.delivery_tag)
    log(f"terminado id={mensaje['id']} -> {resultado}")


def main():
    conexion, canal = conectar()
    declarar(canal, COLA_OPERACIONES)
    if AUTO_ACK:
        # Con auto_ack el prefetch no aplica, el broker empuja todo lo que puede.
        log(f"esperando en '{COLA_OPERACIONES}', auto_ack (sin prefetch)")
    else:
        # Reparto justo, a lo más un mensaje sin confirmar por réplica.
        canal.basic_qos(prefetch_count=1)
        log(f"esperando en '{COLA_OPERACIONES}', prefetch=1, ack manual")
    canal.basic_consume(COLA_OPERACIONES, al_recibir, auto_ack=AUTO_ACK)
    try:
        canal.start_consuming()
    except KeyboardInterrupt:
        conexion.close()


if __name__ == "__main__":
    main()
