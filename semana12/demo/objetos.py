"""
Objetos remotos del servicio, semana 12.

Aquí el dominio deja de exponerse como funciones sueltas (gRPC, JSON-RPC) y
pasa a exponerse como OBJETOS que viven en el servidor.

  Inventario  objeto de entrada, se registra en el servidor de nombres.
              Delega en dominio.py y además fabrica objetos Pedido.
  Pedido      objeto con estado propio (sus líneas). No se registra con
              nombre, el cliente lo recibe POR REFERENCIA desde
              Inventario.abrir_pedido().

Variables
  MODO       single | session | percall   modo de instancia del Inventario
  POR_VALOR  0 | 1   con 1, abrir_pedido devuelve el Pedido sin registrarlo
             en el daemon (experimento, el cliente recibe un error)

El equipo reemplaza Inventario y Pedido por los objetos de su dominio.
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
class Pedido:
    """Pedido en curso. Su estado (las líneas) vive en el servidor.

    El cliente nunca tiene una copia, tiene una referencia remota (un proxy).
    Al confirmar o cancelar, el pedido se desregistra del daemon y cualquier
    referencia que quede apuntando a él pasa a ser una referencia colgante.
    """

    def __init__(self, cliente):
        self.cliente = cliente
        self.lineas = []
        self.creado = time.strftime("%H:%M:%S")

    def agregar(self, producto, cantidad):
        """Agrega una línea al pedido. Todavía no toca el stock."""
        if cantidad <= 0:
            raise dominio.ErrorParametros("cantidad debe ser mayor que cero")
        self.lineas.append((producto, cantidad))
        return len(self.lineas)

    def ver(self):
        """Devuelve una copia (por valor) del estado del pedido."""
        return {"cliente": self.cliente, "creado": self.creado,
                "lineas": [list(l) for l in self.lineas]}

    def confirmar(self):
        """Descuenta el stock de todas las líneas y termina la vida del objeto."""
        resultado = dominio.quitar_varios(self.lineas)
        self._terminar()
        return resultado

    def cancelar(self):
        """Termina la vida del objeto sin tocar el stock."""
        self._terminar()
        return "cancelado"

    def _terminar(self):
        # Desregistrar es el fin del ciclo de vida. Desde aquí, la URI de
        # este objeto ya no existe en el daemon.
        self._pyroDaemon.unregister(self)


@expose
@behavior(instance_mode=MODO)
class Inventario:
    """Objeto de entrada del servicio. Se publica en el servidor de nombres."""

    def __init__(self):
        self.numero = _nueva_instancia()
        self.llamadas = 0

    def _contar(self):
        self.llamadas += 1

    def listar(self):
        self._contar()
        return dominio.listar()

    def agregar(self, producto, cantidad):
        self._contar()
        return dominio.agregar(producto, cantidad)

    def quitar(self, producto, cantidad):
        self._contar()
        return dominio.quitar(producto, cantidad)

    def quien_soy(self):
        """Cuenta qué instancia atendió la llamada y cuántas lleva.

        Sirve para ver el modo de instancia. El stock vive en dominio.py y
        es el mismo para todas las instancias.
        """
        self._contar()
        return {"modo": MODO, "instancia": self.numero, "llamadas": self.llamadas,
                "cliente": str(current_context.client_sock_addr)}

    def pedidos_vivos(self):
        """Cuántos objetos Pedido siguen registrados en el daemon.

        Un pedido que nadie confirma ni cancela queda vivo para siempre.
        Pyro5 no tiene recolector de basura distribuido.
        """
        self._contar()
        return sum(1 for o in self._pyroDaemon.objectsById.values()
                   if isinstance(o, Pedido))

    def abrir_pedido(self, cliente):
        """Fábrica. Crea un Pedido en el servidor y entrega una referencia."""
        self._contar()
        pedido = Pedido(cliente)
        if POR_VALOR:
            # Experimento. Sin registrar, Pyro5 intenta enviar el objeto
            # serializado (por valor) y el cliente lo rechaza.
            return pedido
        self._pyroDaemon.register(pedido)
        return pedido  # autoproxy, viaja como referencia remota
