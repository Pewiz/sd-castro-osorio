"""
Publicador de jugadas, proyecto integrador.

Representa al juego que, al terminar una ronda, deja las jugadas en la cola
'operaciones' y sigue sin esperar al servidor. Cada mensaje lleva un
id_solicitud único, que el servidor usa para no aplicarlo dos veces.

Uso
  docker compose run --rm publicador UNIR ana
  docker compose run --rm publicador ANOTAR david 5
  docker compose run --rm publicador --n 10 ANOTAR david 1
"""
import argparse
import uuid

from cola import COLA_OPERACIONES, conectar, declarar, log, publicar


def main():
    p = argparse.ArgumentParser(description="Publica jugadas en la cola")
    p.add_argument("--n", type=int, default=1, help="cuántas veces publicarla")
    p.add_argument("op", help="UNIR o ANOTAR")
    p.add_argument("args", nargs="*", help="argumentos, por ejemplo david 5")
    a = p.parse_args()

    conexion, canal = conectar()
    declarar(canal, COLA_OPERACIONES)
    for _ in range(a.n):
        # Un id distinto por mensaje. Si el broker lo reentrega, llega con el mismo id.
        mensaje = {"id": uuid.uuid4().hex[:8], "op": a.op.upper(), "args": a.args}
        publicar(canal, COLA_OPERACIONES, mensaje)
        log(f"publicado id={mensaje['id']} {mensaje['op']} {' '.join(a.args)}")
    conexion.close()
    log(f"{a.n} publicados en '{COLA_OPERACIONES}'")


if __name__ == "__main__":
    main()
