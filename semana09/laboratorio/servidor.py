"""servidor.py — servidor TCP con hilo por cliente y mensajes estructurados (Semana 9).

Cada mensaje llega enmarcado y codificado con codec.py (JSON o binario según la variable CODEC).

El dominio es JUEGOS, una tabla de puntajes (TABLA, UNIR, ANOTAR).
"""
import json
import os
import socket
import struct
import threading
import time

import codec
from mensajes import Solicitud, VERSION, ok, error

HOST = "0.0.0.0"
PUERTO = int(os.environ.get("SERVIDOR_PUERTO", "5000"))
TIMEOUT = float(os.environ.get("TIMEOUT_SERVIDOR", "30"))

estado = {"puntajes": {"david": 0, "felipe": 0}, "operaciones": 0}
lock = threading.Lock()


def log(*args):
    print(time.strftime("%H:%M:%S"), f"[{threading.current_thread().name}]", *args, flush=True)


# ---------------------------------------------------------------- dominio
# Dominio JUEGOS (tabla de puntajes).
# Los errores de dominio llevan "CODIGO detalle" en el campo error, así la API
# puede traducir el código a un estado HTTP.
def procesar(sol):
    """Recibe una Solicitud y devuelve una Respuesta. Aquí va el dominio del equipo."""
    op, args = sol.operacion.upper(), sol.argumentos
    if op == "HOLA":
        return ok(sol, [f"HOLA {args[0] if args else 'anonimo'}"])
    if op == "SALIR":
        return ok(sol, ["CHAO"])
    if op == "TABLA":
        with lock:
            estado["operaciones"] += 1
            return ok(sol, [f"{k}:{v}" for k, v in sorted(estado["puntajes"].items())])
    if op == "UNIR":
        if len(args) != 1 or not args[0].strip() or " " in args[0].strip():
            return error(sol.id, "FORMATO UNIR <jugador>")
        jugador = args[0].strip().lower()
        with lock:
            estado["operaciones"] += 1
            if jugador in estado["puntajes"]:
                return error(sol.id, "JUGADOR_YA_EXISTE")
            estado["puntajes"][jugador] = 0
        return ok(sol, [jugador, "0"])
    if op == "ANOTAR":
        if len(args) != 2 or not args[1].isdigit():
            return error(sol.id, "FORMATO ANOTAR <jugador> <puntos>")
        jugador, puntos = args[0].lower(), int(args[1])
        with lock:
            estado["operaciones"] += 1
            if jugador not in estado["puntajes"]:
                return error(sol.id, "JUGADOR_NO_EXISTE")
            actual = estado["puntajes"][jugador]
            time.sleep(0.001)  # ventana para observar la carrera si faltara el Lock
            estado["puntajes"][jugador] = actual + puntos
            nuevo = estado["puntajes"][jugador]
        return ok(sol, [jugador, str(nuevo)])
    if op == "ESPERA":
        try:
            segundos = float(args[0]) if args else 1.0
        except ValueError:
            return error(sol.id, "FORMATO ESPERA <segundos>")
        time.sleep(segundos)  # operación lenta, NO toma el Lock
        return ok(sol, [f"ESPERA {segundos}"])
    return error(sol.id, f"COMANDO_DESCONOCIDO {op}")


# ---------------------------------------------------------------- conexión
def atender(conn, addr):
    conn.settimeout(TIMEOUT)
    log("conectado", addr)
    try:
        while True:
            try:
                sol = codec.recibir(conn, Solicitud)
            except ConnectionError:
                break
            except (struct.error, json.JSONDecodeError, UnicodeDecodeError, ValueError, KeyError, IndexError) as e:
                # Mensaje mal formado. El servidor responde y cierra ESTA conexión, no muere.
                nombre = "struct.error" if isinstance(e, struct.error) else type(e).__name__
                log("mensaje mal formado desde", addr, "->", nombre, e)
                codec.enviar(conn, error(0, f"mensaje mal formado ({nombre})"))
                break
            if sol.version != VERSION:
                log("versión no soportada", sol.version, "desde", addr)
                codec.enviar(conn, error(sol.id, f"versión {sol.version} no soportada, use {VERSION}"))
                continue
            log("solicitud", sol.id, sol.operacion, sol.argumentos)
            resp = procesar(sol)
            codec.enviar(conn, resp)
            if sol.operacion.upper() == "SALIR":
                break
    except socket.timeout:
        log("timeout de", addr, "sin mensajes completos en", TIMEOUT, "s")
    except OSError as e:
        log("error de red con", addr, e)
    finally:
        conn.close()
        log("desconectado", addr)


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PUERTO))
    srv.listen(16)
    log(f"servidor juegos v{VERSION} en {HOST}:{PUERTO}  codec={codec.CODEC}  hilo por cliente")
    n = 0
    while True:
        conn, addr = srv.accept()
        n += 1
        threading.Thread(target=atender, args=(conn, addr), name=f"cli-{n}", daemon=True).start()


if __name__ == "__main__":
    main()
