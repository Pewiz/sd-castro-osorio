"""
Cliente Pyro5 del servicio, semana 12.

Uso (dentro del contenedor cliente, o con Python local)
  python cliente_pyro.py uri
  python cliente_pyro.py listar
  python cliente_pyro.py agregar cafe 10
  python cliente_pyro.py quitar cafe 3
  python cliente_pyro.py quien --veces 3
  python cliente_pyro.py pedido cafe:2 te:1 [--esperar 30]
  python cliente_pyro.py vivos
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
NOMBRE = f"sd.{EQUIPO}.inventario"


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


def inventario():
    """Proxy al Inventario. La URI se resuelve en el servidor de nombres."""
    proxy = Proxy(f"PYRONAME:{NOMBRE}@{NS_HOST}:{NS_PUERTO}")
    proxy._pyroTimeout = 5
    return proxy


def cmd_uri(_):
    with locate_ns(host=NS_HOST, port=NS_PUERTO) as ns:
        log(f"{NOMBRE} -> {ns.lookup(NOMBRE)}")
        log(f"nombres registrados {sorted(ns.list().keys())}")


def cmd_listar(_):
    with inventario() as inv:
        log(f"stock {inv.listar()}")


def cmd_agregar(a):
    with inventario() as inv:
        log(f"agregar -> {inv.agregar(a.producto, a.cantidad)}")


def cmd_quitar(a):
    with inventario() as inv:
        log(f"quitar -> {inv.quitar(a.producto, a.cantidad)}")


def cmd_quien(a):
    """Mismo proxy varias veces y después un proxy nuevo. Muestra el modo."""
    for etiqueta in ("proxy A", "proxy B"):
        with inventario() as inv:
            for _ in range(a.veces):
                log(f"{etiqueta} -> {inv.quien_soy()}")


def cmd_vivos(_):
    with inventario() as inv:
        log(f"pedidos vivos en el servidor {inv.pedidos_vivos()}")


def reintentar_confirmar(uri, segundos):
    """Vuelve a llamar confirmar() sobre la misma URI hasta que el servidor
    conteste. Si contesta 'unknown object', no tiene sentido seguir."""
    limite = time.time() + segundos
    while True:
        try:
            with Proxy(uri) as pedido:
                return pedido.confirmar()
        except CommunicationError as e:
            if "unknown object" in str(e) or time.time() > limite:
                raise
            time.sleep(1)


def cmd_pedido(a):
    lineas = []
    for item in a.lineas:
        producto, _, cantidad = item.partition(":")
        if not (cantidad or "1").isdigit():
            log(f"ERROR de uso. Las líneas van como producto:cantidad, recibí {item}")
            sys.exit(1)
        lineas.append((producto, int(cantidad or 1)))
    with inventario() as inv:
        pedido = inv.abrir_pedido(os.environ.get("HOSTNAME", "cliente"))
        pedido._pyroTimeout = 5
        log(f"recibí {type(pedido).__name__}, referencia {pedido._pyroUri}")
        for producto, cantidad in lineas:
            pedido.agregar(producto, cantidad)
        log(f"estado en el servidor {pedido.ver()}")
        if a.esperar:
            log(f"espero {a.esperar} s antes de confirmar (momento para la falla)")
            time.sleep(a.esperar)
        try:
            resultado = pedido.confirmar()
        except CommunicationError as e:
            log(f"se cortó la conexión ({type(e).__name__}). Reintento con la "
                "MISMA referencia durante 30 s, levanten el servidor")
            resultado = reintentar_confirmar(pedido._pyroUri, 30)
        log(f"confirmar -> {resultado}")
        log("uso la referencia después de confirmar")
        pedido.ver()


def cmd_vigilar(a):
    """Llama listar() cada a.cada segundos con el MISMO proxy y reporta fallas."""
    inv = inventario()
    while True:
        try:
            log(f"ok, stock {inv.listar()}  [{inv._pyroUri}]")
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
    sub.add_parser("listar").set_defaults(f=cmd_listar)
    for nombre, f in (("agregar", cmd_agregar), ("quitar", cmd_quitar)):
        s = sub.add_parser(nombre)
        s.add_argument("producto")
        s.add_argument("cantidad", type=int)
        s.set_defaults(f=f)
    sub.add_parser("vivos").set_defaults(f=cmd_vivos)
    s = sub.add_parser("quien")
    s.add_argument("--veces", type=int, default=3)
    s.set_defaults(f=cmd_quien)
    s = sub.add_parser("pedido")
    s.add_argument("lineas", nargs="+", help="producto:cantidad")
    s.add_argument("--esperar", type=int, default=0)
    s.set_defaults(f=cmd_pedido)
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
