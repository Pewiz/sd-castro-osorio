"""Puerta HTTP (API REST) delante del servidor TCP de la Semana 6.

Cada peticion HTTP se TRADUCE a una linea del protocolo de texto, se envia
al servidor TCP y la respuesta se traduce de vuelta a JSON y a un codigo HTTP.

    GET  /jugadores                      ->  TABLA
    GET  /jugadores/{jugador}            ->  TABLA (y se filtra)
    POST /jugadores                      ->  UNIR <jugador>
    POST /jugadores/{jugador}/puntos     ->  ANOTAR <jugador> <puntos>

Dominio JUEGOS (tabla de puntajes). Se mantiene la estructura
    pedir()     habla con el servidor TCP  (no se toca)
    traducir()  convierte OK / ERROR en datos o en un codigo HTTP  (no se toca)
    ERRORES     tabla codigo del protocolo -> codigo HTTP  (se adapta)
    recursos    una funcion por operacion expuesta  (se adapta)

La API NO guarda nada. Todo el estado sigue viviendo en el servidor TCP.
"""
import os
import socket

from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, Field

SERVIDOR_HOST = os.environ.get("SERVIDOR_HOST", "servidor")
SERVIDOR_PUERTO = int(os.environ.get("SERVIDOR_PUERTO", "5000"))
TIMEOUT_SERVIDOR = float(os.environ.get("TIMEOUT_SERVIDOR", "3"))
REPLICA = os.environ.get("REPLICA", socket.gethostname())

app = FastAPI(title="API de juegos", version="1.0",
              description="Puerta HTTP del servicio propio. Semana 7.")

JUGADOR = Path(pattern=r"^[a-z0-9_]{1,30}$", description="nombre del jugador, sin espacios")

# Codigo de error del protocolo de texto  ->  codigo de estado HTTP
ERRORES = {
    "JUGADOR_NO_EXISTE": 404,       # el recurso no existe
    "JUGADOR_YA_EXISTE": 409,       # la peticion es valida pero choca con el estado actual
    "FORMATO": 400,                 # la peticion esta mal armada
    "COMANDO_DESCONOCIDO": 501,     # el servidor no implementa esa operacion
}


class NuevoJugador(BaseModel):
    jugador: str = Field(pattern=r"^[a-z0-9_]{1,30}$", description="nombre del jugador, sin espacios")


class Anotacion(BaseModel):
    puntos: int = Field(gt=0, description="puntos, entero mayor que cero")


# ----------------------------------------------------------------- hablar con el nivel de datos
def pedir(linea: str) -> str:
    """Envia UNA linea al nivel de datos y devuelve UNA linea de respuesta."""
    try:
        with socket.create_connection((SERVIDOR_HOST, SERVIDOR_PUERTO),
                                      timeout=TIMEOUT_SERVIDOR) as s:
            s.sendall((linea + "\n").encode("utf-8"))
            respuesta = s.makefile("r", encoding="utf-8").readline().strip()
    except socket.timeout:
        raise HTTPException(504, {"error": "SERVIDOR_NO_RESPONDE", "replica": REPLICA})
    except OSError as e:                     # no resuelve el nombre, conexion rechazada, red caida
        raise HTTPException(503, {"error": "SERVIDOR_NO_DISPONIBLE",
                                  "detalle": e.__class__.__name__, "replica": REPLICA})
    if not respuesta:
        raise HTTPException(503, {"error": "SERVIDOR_CERRO_LA_CONEXION", "replica": REPLICA})
    return respuesta


def traducir(respuesta: str) -> list[str]:
    """'OK a b c' -> ['a','b','c'].  'ERROR CODIGO detalle' -> excepcion HTTP."""
    partes = respuesta.split()
    if partes[0] == "OK":
        return partes[1:]
    codigo = partes[1] if len(partes) > 1 else "DESCONOCIDO"
    raise HTTPException(ERRORES.get(codigo, 500),
                        {"error": codigo, "detalle": " ".join(partes[2:]), "replica": REPLICA})


def tabla() -> dict[str, int]:
    pares = (p.split(":") for p in traducir(pedir("TABLA")))
    return {nombre: int(puntos) for nombre, puntos in pares}


# ----------------------------------------------------------------- recursos
@app.get("/salud")
def salud():
    return {"estado": "ok", "replica": REPLICA}


@app.get("/jugadores")
def listar_jugadores():
    return {"jugadores": tabla(), "replica": REPLICA}


@app.get("/jugadores/{jugador}")
def ver_jugador(jugador: str = JUGADOR):
    jugadores = tabla()
    if jugador not in jugadores:
        raise HTTPException(404, {"error": "JUGADOR_NO_EXISTE", "replica": REPLICA})
    return {"jugador": jugador, "puntos": jugadores[jugador], "replica": REPLICA}


@app.post("/jugadores", status_code=201)
def unir_jugador(nuevo: NuevoJugador):
    nombre, puntos = traducir(pedir(f"UNIR {nuevo.jugador}"))
    return {"jugador": nombre, "puntos": int(puntos), "replica": REPLICA}


@app.post("/jugadores/{jugador}/puntos", status_code=201)
def anotar_puntos(anotacion: Anotacion, jugador: str = JUGADOR):
    nombre, total = traducir(pedir(f"ANOTAR {jugador} {anotacion.puntos}"))
    return {"jugador": nombre, "puntos": int(total), "replica": REPLICA}
