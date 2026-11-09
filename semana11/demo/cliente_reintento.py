"""
Cliente JSON-RPC con timeout y reintentos. Demo del jueves, semana 11.

Uso
  python cliente_reintento.py listar
  python cliente_reintento.py agregar tornillo 25
  python cliente_reintento.py agregar tornillo 25 --reintentos 1
  python cliente_reintento.py quitar tornillo 5

Variables
  SERVIDOR_HOST    (servidor)   SERVIDOR_PUERTO (8000)
  TIMEOUT_CLIENTE  (2)          segundos que el cliente espera cada intento
  REINTENTOS       (0)          intentos extra si se agota el timeout

Cada reintento manda EXACTAMENTE la misma petición, con el mismo id.
"""
import argparse
import json
import os
import random
import socket
import urllib.error
import urllib.request

HOST = os.getenv("SERVIDOR_HOST", "servidor")
PUERTO = os.getenv("SERVIDOR_PUERTO", "8000")
URL = f"http://{HOST}:{PUERTO}/rpc"


def llamar(peticion, timeout):
    datos = json.dumps(peticion).encode()
    req = urllib.request.Request(URL, data=datos, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metodo", choices=["listar", "agregar", "quitar"])
    ap.add_argument("producto", nargs="?")
    ap.add_argument("cantidad", nargs="?", type=int)
    ap.add_argument("--reintentos", type=int, default=int(os.getenv("REINTENTOS", "0")))
    ap.add_argument("--timeout", type=float, default=float(os.getenv("TIMEOUT_CLIENTE", "2")))
    a = ap.parse_args()

    params = {} if a.metodo == "listar" else {"producto": a.producto, "cantidad": a.cantidad}
    peticion = {"jsonrpc": "2.0", "method": a.metodo, "params": params, "id": random.randint(1000, 9999)}

    for intento in range(1, a.reintentos + 2):
        print(f"[cliente] intento {intento}, id={peticion['id']}, timeout {a.timeout:.0f} s")
        try:
            resp = llamar(peticion, a.timeout)
        except (socket.timeout, TimeoutError):
            print("[cliente]   timeout, no sé si el servidor lo aplicó")
            continue
        except urllib.error.URLError as e:
            if isinstance(e.reason, (socket.timeout, TimeoutError)):
                print("[cliente]   timeout, no sé si el servidor lo aplicó")
                continue
            print(f"[cliente]   sin conexión ({e.reason})")
            continue
        print(f"[cliente]   respuesta {json.dumps(resp.get('result', resp.get('error')), ensure_ascii=False)}")
        return 0
    print("[cliente] me rendí, la operación quedó en estado DESCONOCIDO")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
