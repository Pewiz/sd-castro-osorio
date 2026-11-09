"""rpc.py — prototipo JSON-RPC 2.0 sobre FastAPI (Semana 10).

Un solo endpoint POST /rpc. Los métodos del dominio se registran en METODOS.
Dominio: juegos, tabla de puntajes (operaciones unir y anotar).

  uvicorn rpc:app --host 0.0.0.0 --port 8000
  curl -s -X POST localhost:8000/rpc -H 'Content-Type: application/json' \
       -d '{"jsonrpc":"2.0","method":"unir","params":{"jugador":"ana"},"id":1}'
"""
import json
from fastapi import FastAPI, Request, Response

app = FastAPI(title="JSON-RPC 2.0 · prototipo semana 10")

# ----------------------------------------------------------------- dominio
# Mismo estado que el servidor TCP: puntajes en memoria del proceso.
puntajes = {"david": 0, "felipe": 0}


def unir(jugador: str):
    if not isinstance(jugador, str) or not jugador.strip() or " " in jugador.strip():
        raise TypeError("jugador debe ser un texto sin espacios")
    jugador = jugador.strip().lower()
    if jugador in puntajes:
        raise ValueError(f"el jugador {jugador} ya existe")
    puntajes[jugador] = 0
    return {"jugador": jugador, "puntos": 0}


def anotar(jugador: str, puntos: int):
    if not isinstance(jugador, str) or not isinstance(puntos, int) or isinstance(puntos, bool):
        raise TypeError("jugador debe ser texto y puntos un entero")
    if puntos <= 0:
        raise ValueError("los puntos deben ser mayores que cero")
    jugador = jugador.lower()
    if jugador not in puntajes:
        raise ValueError(f"el jugador {jugador} no existe")
    puntajes[jugador] += puntos
    return {"jugador": jugador, "puntos": puntajes[jugador]}


METODOS = {"unir": unir, "anotar": anotar}

# ----------------------------------------------------------------- JSON-RPC
PARSE_ERROR, INVALID_REQUEST, METHOD_NOT_FOUND, INVALID_PARAMS, INTERNAL = -32700, -32600, -32601, -32602, -32603
SERVER_ERROR = -32000  # errores del dominio, rango -32000 a -32099


def error(id_, codigo, mensaje, datos=None):
    e = {"code": codigo, "message": mensaje}
    if datos is not None:
        e["data"] = datos
    return {"jsonrpc": "2.0", "error": e, "id": id_}


def atender(req):
    """Procesa UNA solicitud JSON-RPC y devuelve la respuesta, o None si es notificación."""
    if not isinstance(req, dict) or req.get("jsonrpc") != "2.0" or "method" not in req:
        return error(req.get("id") if isinstance(req, dict) else None, INVALID_REQUEST, "Invalid Request")
    id_ = req.get("id")
    es_notificacion = "id" not in req
    metodo = METODOS.get(req["method"])
    if metodo is None:
        return None if es_notificacion else error(id_, METHOD_NOT_FOUND, "Method not found")
    params = req.get("params", [])
    try:
        resultado = metodo(**params) if isinstance(params, dict) else metodo(*params)
    except TypeError as e:
        return None if es_notificacion else error(id_, INVALID_PARAMS, "Invalid params", str(e))
    except ValueError as e:
        return None if es_notificacion else error(id_, SERVER_ERROR, "Error del dominio", str(e))
    except Exception as e:
        return None if es_notificacion else error(id_, INTERNAL, "Internal error", type(e).__name__)
    return None if es_notificacion else {"jsonrpc": "2.0", "result": resultado, "id": id_}


@app.post("/rpc")
async def rpc(request: Request):
    cuerpo = await request.body()
    try:
        datos = json.loads(cuerpo)
    except json.JSONDecodeError:
        return error(None, PARSE_ERROR, "Parse error")
    if isinstance(datos, list):                      # batch
        if not datos:
            return error(None, INVALID_REQUEST, "Invalid Request")
        respuestas = [r for r in (atender(x) for x in datos) if r is not None]
        return respuestas if respuestas else Response(status_code=204)
    resp = atender(datos)
    return resp if resp is not None else Response(status_code=204)
