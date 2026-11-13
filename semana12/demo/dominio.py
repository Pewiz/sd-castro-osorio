"""
Dominio del servicio. Es el mismo archivo de semana11/.

Este archivo es lo que NO cambia cuando cambia el transporte. Lo usaron
rpc.py (JSON-RPC, semana 10) y servidor_grpc.py (gRPC, semana 11), y ahora
lo usa objetos.py (Pyro5, semana 12).

El equipo reemplaza este inventario de referencia por el dominio.py de su
propio semana11/, sin modificarlo.
"""
import threading

_lock = threading.Lock()
_stock = {}


class ErrorDominio(Exception):
    """Regla del negocio que no se cumple, por ejemplo stock insuficiente."""


class ErrorParametros(Exception):
    """Parámetros con valor inválido."""


def _validar(producto, cantidad):
    if not producto:
        raise ErrorParametros("producto vacío")
    if cantidad <= 0:
        raise ErrorParametros("cantidad debe ser mayor que cero")


def listar():
    with _lock:
        return dict(_stock)


def agregar(producto, cantidad):
    _validar(producto, cantidad)
    with _lock:
        _stock[producto] = _stock.get(producto, 0) + cantidad
        return {"producto": producto, "stock": _stock[producto]}


def quitar(producto, cantidad):
    _validar(producto, cantidad)
    with _lock:
        actual = _stock.get(producto, 0)
        if actual < cantidad:
            raise ErrorDominio(f"stock insuficiente, hay {actual}")
        _stock[producto] = actual - cantidad
        return {"producto": producto, "stock": _stock[producto]}


def quitar_varios(lineas):
    """Quita varias líneas de una sola vez. Si una falla, no se aplica ninguna.

    lineas es una lista de pares (producto, cantidad).
    """
    for producto, cantidad in lineas:
        _validar(producto, cantidad)
    with _lock:
        pedido = {}
        for producto, cantidad in lineas:
            pedido[producto] = pedido.get(producto, 0) + cantidad
        for producto, cantidad in pedido.items():
            actual = _stock.get(producto, 0)
            if actual < cantidad:
                raise ErrorDominio(f"stock insuficiente de {producto}, hay {actual}")
        for producto, cantidad in pedido.items():
            _stock[producto] -= cantidad
        return {p: _stock[p] for p in pedido}
