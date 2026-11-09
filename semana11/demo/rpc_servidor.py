"""
Demo del jueves, semana 11. Semánticas de fallo en RPC.

Servidor JSON-RPC 2.0 sobre FastAPI con el dominio de inventario de referencia
(el mismo esqueleto de la semana 10). Agrega dos perillas para provocar fallas.

  FALLA=no        comportamiento normal (valor por defecto)
  FALLA=primera   la PRIMERA operación que modifica estado se aplica y después
                  la respuesta se demora DEMORA segundos (simula una red lenta
                  en el camino de vuelta)
  FALLA=siempre   todas las operaciones que modifican estado se demoran
  DEMORA=3        segundos de demora cuando hay falla
  DEDUP=0|1       con 1 el servidor recuerda la respuesta de cada id y, si llega
                  un reintento con el mismo id, devuelve la respuesta guardada
                  sin volver a aplicar la operación

Correr con  uvicorn rpc_servidor:app --host 0.0.0.0 --port 8000
"""
import json
import os
import threading
import time

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response

FALLA = os.getenv("FALLA", "no")
DEMORA = float(os.getenv("DEMORA", "3"))
DEDUP = os.getenv("DEDUP", "0") == "1"

app = FastAPI()
lock = threading.Lock()
stock = {}            # estado del dominio, en memoria del proceso
respuestas = {}       # id -> respuesta ya enviada (solo se usa con DEDUP=1)
ya_fallo = False      # para FALLA=primera


def log(msg):
    print(f"[servidor] {msg}", flush=True)


class ErrorDominio(Exception):
    pass


# ---------------- dominio de referencia ----------------
def listar():
    with lock:
        return dict(stock)


def agregar(producto, cantidad):
    if not isinstance(producto, str) or not isinstance(cantidad, int) or cantidad <= 0:
        raise TypeError("producto texto y cantidad entera positiva")
    with lock:
        stock[producto] = stock.get(producto, 0) + cantidad
        return {"producto": producto, "stock": stock[producto]}


def quitar(producto, cantidad):
    if not isinstance(producto, str) or not isinstance(cantidad, int) or cantidad <= 0:
        raise TypeError("producto texto y cantidad entera positiva")
    with lock:
        actual = stock.get(producto, 0)
        if actual < cantidad:
            raise ErrorDominio(f"stock insuficiente, hay {actual}")
        stock[producto] = actual - cantidad
        return {"producto": producto, "stock": stock[producto]}


METODOS = {"listar": listar, "agregar": agregar, "quitar": quitar}
MODIFICAN = {"agregar", "quitar"}


# ---------------- protocolo JSON-RPC 2.0 ----------------
def error(code, message, id_, data=None):
    e = {"code": code, "message": message}
    if data is not None:
        e["data"] = data
    return {"jsonrpc": "2.0", "error": e, "id": id_}


def demorar_si_corresponde(metodo):
    global ya_fallo
    if metodo not in MODIFICAN or FALLA == "no":
        return
    if FALLA == "primera" and ya_fallo:
        return
    ya_fallo = True
    log(f"FALLA={FALLA}, operación YA aplicada, demoro la respuesta {DEMORA:.0f} s")
    time.sleep(DEMORA)


def atender(req):
    if not isinstance(req, dict) or req.get("jsonrpc") != "2.0" or "method" not in req:
        return error(-32600, "Invalid Request", None)
    id_ = req.get("id")
    metodo = req["method"]
    params = req.get("params", {})

    if DEDUP and id_ is not None and id_ in respuestas:
        log(f"id={id_} repetido, devuelvo la respuesta guardada SIN aplicar de nuevo")
        return respuestas[id_]

    if metodo not in METODOS:
        return error(-32601, "Method not found", id_)
    try:
        if isinstance(params, list):
            resultado = METODOS[metodo](*params)
        else:
            resultado = METODOS[metodo](**params)
    except ErrorDominio as e:
        resp = error(-32000, "Error del dominio", id_, str(e))
    except TypeError as e:
        return error(-32602, "Invalid params", id_, str(e))
    else:
        resp = {"jsonrpc": "2.0", "result": resultado, "id": id_}

    log(f"id={id_} {metodo} {params} -> {resp.get('result', resp.get('error'))}")
    if DEDUP and id_ is not None:
        respuestas[id_] = resp            # se guarda ANTES de responder
    demorar_si_corresponde(metodo)
    return resp


@app.post("/rpc")
async def rpc(request: Request):
    try:
        req = json.loads(await request.body())
    except ValueError:
        return JSONResponse(error(-32700, "Parse error", None))
    # atender corre en un hilo aparte, así el sleep de una petición
    # no bloquea a las demás
    if isinstance(req, list):
        resps = [await run_in_threadpool(atender, x) for x in req]
        resps = [r for r in resps if r.get("id") is not None]
        return JSONResponse(resps) if resps else Response(status_code=204)
    resp = await run_in_threadpool(atender, req)
    if isinstance(req, dict) and "id" not in req:
        return Response(status_code=204)
    return JSONResponse(resp)


log(f"arranca con FALLA={FALLA} DEMORA={DEMORA:.0f} DEDUP={int(DEDUP)}")
