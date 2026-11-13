"""
Cliente Pyro5 del servicio, semana 12.

Uso (dentro del contenedor cliente, o con Python local)
  python cliente_pyro.py uri
  python cliente_pyro.py tabla
  python cliente_pyro.py unir ana
  python cliente_pyro.py anotar david 3
  python cliente_pyro.py quien --veces 3
  python cliente_pyro.py partida david 5 [--esperar 30]
  python cliente_pyro.py vivas
  python cliente_pyro.py vigilar [--cada 1]

Variables
  NOMBRES_HOST (nombres)  NOMBRES_PUERTO (9090)  EQUIPO (referencia)
"""
import argparse
import os
import sys
import time

from Pyro5.api import Proxy, locate_ns, register_dict_to_class
from Pyro5.errors import (CommunicationError, DaemonError, NamingError,
                          SerializeError, get_pyro_traceback)

NS_HOST = os.environ.get("NOMBRES_HOST", "nombres")
NS_PUERTO = int(os.environ.get("NOMBRES_PUERTO", "9090"))
EQUIPO = os.environ.get("EQUIPO", "referencia")
NOMBRE = f"sd.{EQUIPO}.juegos"


# Las excepciones también viajan serializadas (por valor). Pyro5 solo sabe
# reconstruir las de Python. Las propias del dominio hay que enseñárselas.
import dominio  # noqa: E402


def _a_excepcion(nombre_clase, datos):
    clase = getattr(dominio, nombre_clase.split(".")[-1])
    return clase(*datos.get("args", ()))


for _nombre in ("ErrorDominio", "ErrorParametros"):
    register_dict_to_class(f"dominio.{_nombre}", _a_excepcion)


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def juegos():
    """Proxy a Juegos. La URI se resuelve en el servidor de nombres."""
    proxy = Proxy(f"PYRONAME:{NOMBRE}@{NS_HOST}:{NS_PUERTO}")
    proxy._pyroTimeout = 5
    return proxy


def cmd_uri(_):
    with locate_ns(host=NS_HOST, port=NS_PUERTO) as ns:
        log(f"{NOMBRE} -> {ns.lookup(NOMBRE)}")
        log(f"nombres registrados {sorted(ns.list().keys())}")


def cmd_tabla(_):
    with juegos() as j:
        log(f"tabla {j.tabla()}")


def cmd_unir(a):
    with juegos() as j:
        log(f"unir -> {j.unir(a.jugador)}")


def cmd_anotar(a):
    with juegos() as j:
        log(f"anotar -> {j.anotar(a.jugador, a.puntos)}")


def cmd_quien(a):
    """Mismo proxy varias veces y después un proxy nuevo. Muestra el modo."""
    for etiqueta in ("proxy A", "proxy B"):
        with juegos() as j:
            for _ in range(a.veces):
                log(f"{etiqueta} -> {j.quien_soy()}")


def cmd_vivas(_):
    with juegos() as j:
        log(f"partidas vivas en el servidor {j.partidas_vivas()}")


def reintentar_finalizar(uri, segundos):
    """Vuelve a llamar finalizar() sobre la misma URI hasta que el servidor
    conteste. Si contesta 'unknown object', no tiene sentido seguir."""
    limite = time.time() + segundos
    while True:
        try:
            with Proxy(uri) as partida:
                return partida.finalizar()
        except CommunicationError as e:
            if "unknown object" in str(e) or time.time() > limite:
                raise
            time.sleep(1)


def cmd_partida(a):
    with juegos() as j:
        partida = j.abrir_partida(a.jugador)
        partida._pyroTimeout = 5
        log(f"recibí {type(partida).__name__}, referencia {partida._pyroUri}")
        partida.sumar(a.puntos)
        log(f"estado en el servidor {partida.ver()}")
        if a.esperar:
            log(f"espero {a.esperar} s antes de finalizar (momento para la falla)")
            time.sleep(a.esperar)
        try:
            resultado = partida.finalizar()
        except CommunicationError as e:
            log(f"se cortó la conexión ({type(e).__name__}). Reintento con la "
                "MISMA referencia durante 30 s, levanten el servidor")
            resultado = reintentar_finalizar(partida._pyroUri, 30)
        log(f"finalizar -> {resultado}")
        log("uso la referencia después de finalizar")
        partida.ver()


def cmd_vigilar(a):
    """Llama tabla() cada a.cada segundos con el MISMO proxy y reporta fallas."""
    inv = juegos()
    while True:
        try:
            log(f"ok, tabla {inv.tabla()}  [{inv._pyroUri}]")
        except CommunicationError as e:
            log(f"FALLA de comunicación {type(e).__name__} {e}")
            try:
                inv._pyroReconnect(tries=1)
                log("reconectado")
            except (CommunicationError, NamingError) as e2:
                log(f"no pude reconectar {type(e2).__name__}")
        except NamingError as e:
            log(f"FALLA de nombres {e}")
        time.sleep(a.cada)


def main():
    p = argparse.ArgumentParser(description="Cliente Pyro5, semana 12")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("uri").set_defaults(f=cmd_uri)
    sub.add_parser("tabla").set_defaults(f=cmd_tabla)
    s = sub.add_parser("unir")
    s.add_argument("jugador")
    s.set_defaults(f=cmd_unir)
    s = sub.add_parser("anotar")
    s.add_argument("jugador")
    s.add_argument("puntos", type=int)
    s.set_defaults(f=cmd_anotar)
    sub.add_parser("vivas").set_defaults(f=cmd_vivas)
    s = sub.add_parser("quien")
    s.add_argument("--veces", type=int, default=3)
    s.set_defaults(f=cmd_quien)
    s = sub.add_parser("partida")
    s.add_argument("jugador")
    s.add_argument("puntos", type=int)
    s.add_argument("--esperar", type=int, default=0)
    s.set_defaults(f=cmd_partida)
    s = sub.add_parser("vigilar")
    s.add_argument("--cada", type=float, default=1)
    s.set_defaults(f=cmd_vigilar)
    a = p.parse_args()
    try:
        a.f(a)
    except KeyboardInterrupt:
        pass
    except NamingError as e:
        log(f"ERROR de nombres. No encuentro {NOMBRE}. {e}")
        sys.exit(2)
    except DaemonError as e:
        log(f"ERROR del daemon. La referencia apunta a un objeto que ya no existe. {e}")
        sys.exit(3)
    except SerializeError as e:
        log(f"ERROR de serialización. El servidor intentó enviar un objeto por valor. {e}")
        sys.exit(4)
    except CommunicationError as e:
        if "unknown object" in str(e):
            log("ERROR. El servidor responde, pero el objeto de esa referencia "
                f"ya no existe (referencia colgante). {e}")
            sys.exit(3)
        log(f"ERROR de comunicación. {type(e).__name__} {e}")
        sys.exit(5)
    except Exception as e:  # error del dominio que viene desde el servidor
        log(f"ERROR remoto {type(e).__name__} {e}")
        if os.environ.get("TRAZA") == "1":
            print("".join(get_pyro_traceback()))
        sys.exit(6)


if __name__ == "__main__":
    main()
