"""
Dominio del servicio de juegos (tabla de puntajes), sin nada de red. Semana 11.

Este archivo es lo que NO cambia cuando cambia el transporte. Lo usan
rpc.py (JSON-RPC) y servidor_grpc.py (gRPC).
"""
import threading

_lock = threading.Lock()
_puntajes = {"david": 0, "felipe": 0}


class ErrorDominio(Exception):
    """Regla del negocio que no se cumple, por ejemplo un jugador que no existe."""


class ErrorParametros(Exception):
    """Parámetros con valor inválido."""


def tabla():
    with _lock:
        return dict(_puntajes)


def unir(jugador):
    if not jugador or not jugador.strip() or " " in jugador.strip():
        raise ErrorParametros("jugador debe ser un texto sin espacios")
    jugador = jugador.strip().lower()
    with _lock:
        if jugador in _puntajes:
            raise ErrorDominio(f"el jugador {jugador} ya existe")
        _puntajes[jugador] = 0
        return {"jugador": jugador, "puntos": 0}


def anotar(jugador, puntos):
    if not jugador:
        raise ErrorParametros("jugador vacío")
    if puntos <= 0:
        raise ErrorParametros("los puntos deben ser mayores que cero")
    jugador = jugador.lower()
    with _lock:
        if jugador not in _puntajes:
            raise ErrorDominio(f"el jugador {jugador} no existe")
        _puntajes[jugador] += puntos
        return {"jugador": jugador, "puntos": _puntajes[jugador]}
