"""
Objetos remotos del servicio, semana 12.

Aquí el dominio deja de exponerse como funciones sueltas (gRPC, JSON-RPC) y
pasa a exponerse como OBJETOS que viven en el servidor.

  Juegos      objeto de entrada, se registra en el servidor de nombres.
              Delega en dominio.py y además fabrica objetos Partida.
  Partida     objeto con estado propio (los puntos de la partida). No se
              registra con nombre, el cliente lo recibe POR REFERENCIA desde
              Juegos.abrir_partida().

Variables
  MODO       single | session | percall   modo de instancia de Juegos
  POR_VALOR  0 | 1   con 1, abrir_partida devuelve la Partida sin registrarla
             en el daemon (experimento, el cliente recibe un error)
"""
import os
import threading
import time

from Pyro5.api import behavior, current_context, expose

import dominio

MODO = os.environ.get("MODO", "single")
POR_VALOR = os.environ.get("POR_VALOR", "0") == "1"

_contador_instancias = 0
_lock_contador = threading.Lock()


def _nueva_instancia():
    global _contador_instancias
    with _lock_contador:
        _contador_instancias += 1
        return _contador_instancias


@expose
class Partida:
    """Partida en curso. Acumula puntos en el servidor y los aplica a la
    tabla al finalizar. Viaja por referencia."""
    def __init__(self, jugador):
        self.jugador, self.puntos = jugador, 0

    def sumar(self, puntos):
        """Cambia estado (de la partida). No toca la tabla."""
        if puntos <= 0:
            raise dominio.ErrorParametros("los puntos deben ser mayores que cero")
        self.puntos += puntos
        return self.puntos

    def ver(self):
        """Consulta. Devuelve una copia (por valor) del estado."""
        return {"jugador": self.jugador, "puntos": self.puntos}

    def finalizar(self):
        """Cambia estado. Aplica los puntos a la tabla y termina la vida del objeto."""
        r = dominio.anotar(self.jugador, self.puntos) if self.puntos else dominio.tabla()
        self._terminar()
        return r

    def cancelar(self):
        """Termina la vida del objeto sin tocar la tabla."""
        self._terminar()
        return "cancelada"

    def _terminar(self):
        self._pyroDaemon.unregister(self)


@expose
@behavior(instance_mode=MODO)
class Juegos:
    """Objeto de entrada del servicio de juegos. Se publica en el servidor de nombres."""

    def __init__(self):
        self.numero = _nueva_instancia()
        self.llamadas = 0

    def _contar(self):
        self.llamadas += 1

    def tabla(self):
        """Consulta. Devuelve la tabla de puntajes. No cambia estado."""
        self._contar()
        return dominio.tabla()

    def unir(self, jugador):
        """Cambia estado. Agrega un jugador nuevo con 0 puntos."""
        self._contar()
        return dominio.unir(jugador)

    def anotar(self, jugador, puntos):
        """Cambia estado. Suma puntos a un jugador existente."""
        self._contar()
        return dominio.anotar(jugador, puntos)

    def quien_soy(self):
        """Consulta. Dice qué instancia atendió la llamada y cuántas lleva.

        Sirve para ver el modo de instancia. La tabla vive en dominio.py y
        es la misma para todas las instancias.
        """
        self._contar()
        return {"modo": MODO, "instancia": self.numero, "llamadas": self.llamadas,
                "cliente": str(current_context.client_sock_addr)}

    def partidas_vivas(self):
        """Consulta. Cuántos objetos Partida siguen registrados en el daemon.

        Una partida que nadie finaliza ni cancela queda viva para siempre.
        Pyro5 no tiene recolector de basura distribuido.
        """
        self._contar()
        return sum(1 for o in self._pyroDaemon.objectsById.values()
                   if isinstance(o, Partida))

    def abrir_partida(self, jugador):
        """Cambia estado (crea un objeto). Fábrica de Partida, entrega una
        referencia remota. El jugador debe existir en la tabla."""
        self._contar()
        jugador = jugador.strip().lower()
        if jugador not in dominio.tabla():
            raise dominio.ErrorDominio(f"el jugador {jugador} no existe")
        partida = Partida(jugador)
        if POR_VALOR:
            # Experimento. Sin registrar, Pyro5 intenta enviar el objeto
            # serializado (por valor) y el cliente lo rechaza.
            return partida
        self._pyroDaemon.register(partida)
        return partida  # autoproxy, viaja como referencia remota
