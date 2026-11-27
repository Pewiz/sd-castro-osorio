"""
Worker del patrón master-worker, semana 13 (paso 4).

Toma un trozo [desde, hasta) de la cola 'tareas_primos', cuenta los primos
de ese trozo y publica el resultado en 'resultados_primos'. No guarda nada
entre trozos (sin estado), por eso se escala con --scale worker=N.

El ack va AL FINAL, después de publicar el resultado. Si el worker muere a
la mitad, el trozo vuelve a la cola y lo toma otro.
"""
import json
import time

from cola import COLA_RESULTADOS, COLA_TAREAS, REPLICA, conectar, declarar, log, publicar


def es_primo(n):
    """División de prueba con 6k±1. Lenta a propósito, es trabajo de CPU."""
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    if n % 3 == 0:
        return n == 3
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def contar_primos(desde, hasta):
    return sum(1 for n in range(desde, hasta) if es_primo(n))


def al_recibir(canal, metodo, props, cuerpo):
    tarea = json.loads(cuerpo)
    t0 = time.perf_counter()
    primos = contar_primos(tarea["desde"], tarea["hasta"])
    segundos = time.perf_counter() - t0
    publicar(canal, COLA_RESULTADOS, {
        "corrida": tarea["corrida"], "trozo": tarea["trozo"], "primos": primos,
        "worker": REPLICA, "segundos": segundos})
    canal.basic_ack(delivery_tag=metodo.delivery_tag)
    log(f"trozo {tarea['trozo']:2d} [{tarea['desde']:,}, {tarea['hasta']:,}) "
        f"-> {primos:,} primos en {segundos:.2f}s")


def main():
    conexion, canal = conectar()
    declarar(canal, COLA_TAREAS)
    declarar(canal, COLA_RESULTADOS)
    canal.basic_qos(prefetch_count=1)   # reparto justo, un trozo a la vez
    canal.basic_consume(COLA_TAREAS, al_recibir)
    log(f"worker listo, esperando trozos en '{COLA_TAREAS}'")
    try:
        canal.start_consuming()
    except KeyboardInterrupt:
        conexion.close()


if __name__ == "__main__":
    main()
