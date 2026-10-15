"""Cliente HTTP minimo (solo biblioteca estandar), para usar desde el contenedor cliente.

  python cliente_http.py GET /jugadores
  python cliente_http.py POST /jugadores jugador=ana
  python cliente_http.py POST /jugadores/felipe/puntos puntos=5
  python cliente_http.py --repetir 6 GET /jugadores/felipe
  python cliente_http.py --repetir 100 --paralelo 10 POST /jugadores/felipe/puntos puntos=1

Los pares clave=valor se envian como cuerpo JSON. La direccion base sale de API_URL.
"""
import argparse
import json
import os
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import urllib.error
import urllib.request

API_URL = os.environ.get("API_URL", "http://nginx")


def pedir(metodo, ruta, cuerpo):
    datos = json.dumps(cuerpo).encode("utf-8") if cuerpo else None
    req = urllib.request.Request(API_URL + ruta, data=datos, method=metodo,
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            estado, texto = r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        estado, texto = e.code, e.read().decode("utf-8")
    except (urllib.error.URLError, OSError) as e:
        estado, texto = 0, f"SIN RESPUESTA ({getattr(e, 'reason', e)})"
    return estado, texto.strip(), time.perf_counter() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metodo", choices=["GET", "POST", "PUT", "DELETE"])
    ap.add_argument("ruta")
    ap.add_argument("campos", nargs="*", help="pares clave=valor para el cuerpo JSON")
    ap.add_argument("--repetir", type=int, default=1)
    ap.add_argument("--paralelo", type=int, default=1,
                    help="peticiones simultaneas; con mas de 1 se imprime solo el resumen")
    args = ap.parse_args()

    cuerpo = {}
    for campo in args.campos:
        clave, _, valor = campo.partition("=")
        cuerpo[clave] = int(valor) if valor.lstrip("-").isdigit() else valor

    if args.paralelo <= 1:
        for _ in range(args.repetir):
            estado, texto, seg = pedir(args.metodo, args.ruta, cuerpo)
            print(f"{estado}  {seg:5.2f} s  {texto}")
        return

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.paralelo) as hilos:
        resultados = list(hilos.map(lambda _: pedir(args.metodo, args.ruta, cuerpo),
                                    range(args.repetir)))
    total = time.perf_counter() - t0
    codigos = Counter(estado for estado, _, _ in resultados)
    replicas = Counter()
    for _, texto, _ in resultados:
        try:
            replicas[json.loads(texto).get("replica", "?")] += 1
        except (ValueError, AttributeError):
            replicas["?"] += 1
    print(f"{args.repetir} peticiones, {args.paralelo} a la vez, {total:.2f} s")
    print(f"codigos   {dict(codigos)}")
    print(f"replicas  {dict(replicas)}")


if __name__ == "__main__":
    main()
