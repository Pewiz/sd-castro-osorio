"""
Piezas comunes de las colas, proyecto integrador (de la semana 13).

Lo usan publicador.py y procesador.py. Aquí está lo que se repetiría en
cada script: la conexión al broker con reintentos, el nombre de la cola y
cómo se publica un mensaje persistente.

Variables
  RABBIT_HOST  (rabbitmq)  nombre del servicio del broker en sd_net
  RABBIT_PORT  (5672)      puerto AMQP
"""
import json
import os
import socket
import time

import pika
from pika.exceptions import AMQPConnectionError

RABBIT_HOST = os.environ.get("RABBIT_HOST", "rabbitmq")
RABBIT_PORT = int(os.environ.get("RABBIT_PORT", "5672"))

# Nombre de la cola. Con el exchange por defecto ("") la routing key es el
# nombre de la cola.
COLA_OPERACIONES = "operaciones"   # jugadas que los procesadores aplican en el servidor

# Identificador corto de la réplica. En Docker el hostname es el id del
# contenedor, así cada réplica de --scale se distingue en los logs.
REPLICA = socket.gethostname()[:6]


def log(msg):
    print(time.strftime("[%H:%M:%S]"), f"[{REPLICA}]", msg, flush=True)


def conectar(intentos=30):
    """Abre conexión y canal con el broker. Reintenta mientras RabbitMQ arranca."""
    parametros = pika.ConnectionParameters(RABBIT_HOST, RABBIT_PORT)
    for i in range(1, intentos + 1):
        try:
            conexion = pika.BlockingConnection(parametros)
            return conexion, conexion.channel()
        except AMQPConnectionError:
            log(f"broker no disponible, intento {i}/{intentos}")
            time.sleep(2)
    raise SystemExit("no pude conectarme al broker, ¿está arriba rabbitmq?")


def declarar(canal, cola):
    """Cola durable, sobrevive a un reinicio del broker."""
    canal.queue_declare(queue=cola, durable=True)


def publicar(canal, cola, datos):
    """Publica un dict como JSON. delivery_mode=2 lo escribe a disco (persistente)."""
    canal.basic_publish(exchange="", routing_key=cola,
                        body=json.dumps(datos).encode(),
                        properties=pika.BasicProperties(delivery_mode=2))
