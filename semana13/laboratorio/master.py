"""
Master del patrón master-worker, semana 13 (paso 4).

Cada corrida
  1. Vacía las colas viejas (restos de una corrida cortada).
  2. Pregunta al broker cuántos workers están consumiendo 'tareas_primos'.
  3. Parte [2, N) en TROZOS trozos y los publica (persistentes).
  4. Junta un resultado por trozo desde 'resultados_primos' y mide el tiempo.
  5. Valida el total contra una criba de Eratóstenes (ok=True).
  6. Agrega una fila a mediciones/mediciones.csv.

Uso
  docker compose run --rm master
  docker compose run --rm master --n 2000000 --trozos 20
  docker compose run --rm master --csv mediciones/experimento.csv

Variables
  N       (5000000)  fin del rango, no incluido
  TROZOS  (40)       cuántos trozos se publican
"""
import argparse
import csv
import json
import os
import time
import uuid

from cola import COLA_RESULTADOS, COLA_TAREAS, conectar, declarar, log, publicar

CSV = "mediciones/mediciones.csv"
COLUMNAS = ["fecha", "workers", "n", "trozos", "segundos", "primos", "ok"]


def criba(n):
    """Cuenta los primos menores que n con la criba de Eratóstenes. Solo valida."""
    es = bytearray([1]) * n
    es[0:2] = b"\x00\x00"
    for i in range(2, int(n ** 0.5) + 1):
        if es[i]:
            es[i * i::i] = bytearray(len(range(i * i, n, i)))
    return sum(es)


def trozos(n, cuantos):
    """Parte [2, n) en 'cuantos' trozos del mismo largo."""
    largo = (n - 2) // cuantos
    limites = [2 + i * largo for i in range(cuantos)] + [n]
    return [(limites[i], limites[i + 1]) for i in range(cuantos)]


def main():
    p = argparse.ArgumentParser(description="Master, reparte el conteo de primos")
    p.add_argument("--n", type=int, default=int(os.environ.get("N", "5000000")))
    p.add_argument("--trozos", type=int, default=int(os.environ.get("TROZOS", "40")))
    p.add_argument("--espera", type=int, default=300, help="segundos máximos sin resultados")
    p.add_argument("--csv", default=CSV, help="archivo donde se agrega la fila")
    a = p.parse_args()

    conexion, canal = conectar()
    declarar(canal, COLA_TAREAS)
    declarar(canal, COLA_RESULTADOS)

    # 1. Vaciar colas viejas
    canal.queue_purge(COLA_TAREAS)
    canal.queue_purge(COLA_RESULTADOS)

    # 2. ¿Cuántos workers hay? El broker sabe cuántos consumidores tiene la cola.
    workers = canal.queue_declare(queue=COLA_TAREAS, durable=True,
                                  passive=True).method.consumer_count
    if workers == 0:
        log("no hay workers. Levántenlos con docker compose up -d --scale worker=1 worker")
        raise SystemExit(1)
    log(f"workers conectados {workers}, publicando {a.trozos} trozos de [2, {a.n:,})")

    # 3. Publicar los trozos. El reloj parte aquí.
    corrida = uuid.uuid4().hex[:6]
    t0 = time.perf_counter()
    for i, (desde, hasta) in enumerate(trozos(a.n, a.trozos)):
        publicar(canal, COLA_TAREAS, {"corrida": corrida, "trozo": i,
                                      "desde": desde, "hasta": hasta})

    # 4. Juntar un resultado por trozo
    resultados = {}
    for metodo, props, cuerpo in canal.consume(COLA_RESULTADOS, inactivity_timeout=a.espera):
        if metodo is None:
            log(f"pasaron {a.espera} s sin resultados, corto la corrida")
            break
        r = json.loads(cuerpo)
        canal.basic_ack(delivery_tag=metodo.delivery_tag)
        if r["corrida"] == corrida:
            resultados[r["trozo"]] = r   # por trozo, un repetido no cuenta dos veces
        if len(resultados) == a.trozos:
            break
    canal.cancel()
    segundos = time.perf_counter() - t0
    conexion.close()

    # Resumen por worker
    por_worker = {}
    for r in resultados.values():
        w = por_worker.setdefault(r["worker"], [0, 0.0])
        w[0] += 1
        w[1] += r["segundos"]
    print(f"{'worker':10}{'trozos':>8}{'seg ocupado':>14}")
    for nombre, (cuantos, ocupado) in sorted(por_worker.items()):
        print(f"{nombre:10}{cuantos:>8}{ocupado:>14.2f}")
    print("-" * 40)

    # 5. Validar contra la criba (fuera del tiempo medido)
    primos = sum(r["primos"] for r in resultados.values())
    esperado = criba(a.n)
    ok = len(resultados) == a.trozos and primos == esperado
    print(f"workers={workers}  tiempo total={segundos:.2f}s")
    print(f"primos={primos:,}  esperado={esperado:,}  ok={ok}")

    # 6. Una fila al CSV
    os.makedirs(os.path.dirname(a.csv) or ".", exist_ok=True)
    nuevo = not os.path.exists(a.csv)
    with open(a.csv, "a", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        if nuevo:
            escritor.writerow(COLUMNAS)
        escritor.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), workers, a.n,
                           a.trozos, round(segundos, 3), primos, ok])
    print(f"fila agregada a {a.csv}")


if __name__ == "__main__":
    main()
