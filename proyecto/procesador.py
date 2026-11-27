"""
Procesador de jugadas, proyecto integrador.

Consume la cola 'operaciones' y aplica cada jugada en el SERVIDOR REAL
(objeto Juegos de Pyro5, buscado por nombre en el servidor de nombres).
No guarda estado propio, el estado vive en el servidor. Por eso corre con
dos o más réplicas y cada jugada la toma una sola.

Qué hace con cada mensaje
  aplicada o repetida      basic_ack, el broker la borra
  error del dominio        basic_reject sin reencolar (venenosa, fallaría siempre)
  servidor o nombres caído basic_nack con reencolar, se reintenta en REINTENTO s

Variables
  NOMBRES_HOST, NOMBRES_PUERTO, EQUIPO   para encontrar sd.<EQUIPO>.juegos
  DEMORA     (0)  segundos entre aplicar en el servidor y el ack. Sirve para
                  matar la réplica justo en ese momento y ver la deduplicación
  REINTENTO  (2)  segundos de espera antes de devolver un mensaje a la cola
"""
import json
import os
import time

from Pyro5.errors import CommunicationError, NamingError

import dominio
from cliente_pyro import juegos   # también registra ErrorDominio y ErrorParametros
from cola import COLA_OPERACIONES, conectar, declarar, log

DEMORA = float(os.environ.get("DEMORA", "0"))
REINTENTO = float(os.environ.get("REINTENTO", "2"))

# Solo operaciones que cambian estado. TABLA no tiene sentido por una cola,
# quien publica no recibe la respuesta. Se consulta directo con cliente_pyro.py.
OPERACIONES_VALIDAS = {"UNIR", "ANOTAR"}

_proxy = None


def servidor():
    """Proxy a Juegos. Se crea la primera vez y después de cada falla."""
    global _proxy
    if _proxy is None:
        _proxy = juegos()
    return _proxy


def olvidar_servidor():
    """Tras una falla se descarta el proxy, así el próximo vuelve a preguntar
    al servidor de nombres (el servidor pudo volver en otra dirección)."""
    global _proxy
    if _proxy is not None:
        _proxy._pyroRelease()
    _proxy = None


def al_recibir(canal, metodo, props, cuerpo):
    m = json.loads(cuerpo)
    marca = " (REENTREGADO)" if metodo.redelivered else ""
    log(f"recibido id={m['id']} {m['op']} {' '.join(m['args'])}{marca}")

    if m["op"] not in OPERACIONES_VALIDAS:
        log(f"descartado id={m['id']}, operación desconocida {m['op']}")
        canal.basic_reject(delivery_tag=metodo.delivery_tag, requeue=False)
        return

    try:
        r = servidor().aplicar(m["id"], m["op"], m["args"])
    except (dominio.ErrorDominio, dominio.ErrorParametros) as e:
        log(f"descartado id={m['id']}, el dominio la rechazó: {e}")
        canal.basic_reject(delivery_tag=metodo.delivery_tag, requeue=False)
        return
    except (CommunicationError, NamingError) as e:
        log(f"servidor no disponible ({type(e).__name__}), id={m['id']} vuelve a la cola")
        olvidar_servidor()
        time.sleep(REINTENTO)
        canal.basic_nack(delivery_tag=metodo.delivery_tag, requeue=True)
        return

    if DEMORA and not r["repetida"]:
        log(f"id={m['id']} aplicada en el servidor, espero {DEMORA:g} s antes del ack ...")
        time.sleep(DEMORA)
    canal.basic_ack(delivery_tag=metodo.delivery_tag)
    if r["repetida"]:
        log(f"id={m['id']} ya estaba aplicada, el servidor no la repitió")
    else:
        log(f"aplicada id={m['id']} -> {r['jugador']} tiene {r['puntos']} puntos")


def main():
    conexion, canal = conectar()
    declarar(canal, COLA_OPERACIONES)
    canal.basic_qos(prefetch_count=1)
    canal.basic_consume(COLA_OPERACIONES, al_recibir)
    log(f"esperando en '{COLA_OPERACIONES}', prefetch=1, ack manual, servidor real por Pyro5")
    try:
        canal.start_consuming()
    except KeyboardInterrupt:
        conexion.close()


if __name__ == "__main__":
    main()
