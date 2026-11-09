"""Puerta HTTP (API REST) delante del servidor TCP.

Cada peticion HTTP se TRADUCE a una Solicitud estructurada, se envia con codec.py
(json o bin segun CODEC) y la Respuesta se traduce de vuelta a JSON y a un codigo HTTP.

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
import struct

import codec
from fastapi import FastAPI, HTTPException, Path
from mensajes import Solicitud, Respuesta
from pydantic import BaseModel, Field

SERVIDOR_HOST = os.environ.get("SERVIDOR_HOST", "servidor")
SERVIDOR_PUERTO = int(os.environ.get("SERVIDOR_PUERTO", "5000"))
TIMEOUT_SERVIDOR = float(os.environ.get("TIMEOUT_SERVIDOR", "3"))
REPLICA = os.environ.get("REPLICA", socket.gethostname())

app = FastAPI(title="API de juegos", version="1.0",
              description="Puerta HTTP del servicio propio..")

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
def pedir(operacion: str, *argumentos: str) -> Respuesta:
    """Envia UNA solicitud estructurada al nivel de datos (codec json o bin) y devuelve la Respuesta."""
    try:
        with socket.create_connection((SERVIDOR_HOST, SERVIDOR_PUERTO),
                                      timeout=TIMEOUT_SERVIDOR) as s:
            codec.enviar(s, Solicitud(operacion=operacion, argumentos=list(argumentos), id=1))
            return codec.recibir(s, Respuesta)
    except socket.timeout:
        raise HTTPException(504, {"error": "SERVIDOR_NO_RESPONDE", "replica": REPLICA})
    except (struct.error, ValueError, KeyError, UnicodeDecodeError) as e:
        # respuesta que no se puede decodificar (codec distinto en los dos lados)
        raise HTTPException(503, {"error": "RESPUESTA_ILEGIBLE",
                                  "detalle": e.__class__.__name__, "replica": REPLICA})
    except OSError as e:                     # rechazada, red caida, o cerro sin responder (ConnectionError)
        raise HTTPException(503, {"error": "SERVIDOR_NO_DISPONIBLE",
                                  "detalle": e.__class__.__name__, "replica": REPLICA})


def traducir(respuesta: Respuesta) -> list[str]:
    """OK -> datos.  ERROR 'CODIGO detalle' -> excepcion HTTP."""
    if respuesta.estado == "OK":
        return respuesta.datos
    partes = respuesta.error.split()
    codigo = partes[0] if partes else "DESCONOCIDO"
    raise HTTPException(ERRORES.get(codigo, 500),
                        {"error": codigo, "detalle": " ".join(partes[1:]), "replica": REPLICA})


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
    nombre, puntos = traducir(pedir("UNIR", nuevo.jugador))
    return {"jugador": nombre, "puntos": int(puntos), "replica": REPLICA}


@app.post("/jugadores/{jugador}/puntos", status_code=201)
def anotar_puntos(anotacion: Anotacion, jugador: str = JUGADOR):
    nombre, total = traducir(pedir("ANOTAR", jugador, str(anotacion.puntos)))
    return {"jugador": nombre, "puntos": int(total), "replica": REPLICA}
