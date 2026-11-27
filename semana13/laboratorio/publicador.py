"""
Publicador de operaciones del dominio, semana 13 (pasos 2 y 3).

Deja operaciones del servicio de juegos en la cola durable 'operaciones'.
No espera respuesta y no necesita que el procesador esté vivo, el broker
las guarda hasta que alguien las consuma.

Uso
  docker compose run --rm publicador ANOTAR david 5
  docker compose run --rm publicador --n 20 ANOTAR david 1
  docker compose run --rm publicador UNIR ana
  docker compose run --rm publicador TABLA
  docker compose run --rm publicador BORRAR david     (venenoso, se descarta)
"""
import argparse

from cola import COLA_OPERACIONES, conectar, declarar, log, publicar


def main():
    p = argparse.ArgumentParser(description="Publica operaciones en la cola")
    p.add_argument("--n", type=int, default=1, help="cuántas veces publicarla")
    p.add_argument("op", help="operación, por ejemplo ANOTAR")
    p.add_argument("args", nargs="*", help="argumentos de la operación")
    a = p.parse_args()

    conexion, canal = conectar()
    declarar(canal, COLA_OPERACIONES)
    for i in range(1, a.n + 1):
        mensaje = {"id": i, "op": a.op.upper(), "args": a.args}
        publicar(canal, COLA_OPERACIONES, mensaje)
        log(f"publicado id={mensaje['id']} {mensaje['op']} {' '.join(a.args)}")
    conexion.close()
    log(f"{a.n} publicados en '{COLA_OPERACIONES}'")


if __name__ == "__main__":
    main()
