# Observaciones, taller semana 12 (objetos distribuidos con Pyro5)

Equipo castro-osorio
Integrantes presentes
Fecha 13-11-2026

## Paso 1, nombres y servidor arriba

URI que entregó el servidor de nombres para `sd.<equipo>.juegos`
(pegar la salida de `python cliente_pyro.py uri`)

```
18:21:50 sd.castro-osorio.juegos -> PYRO:juegos@servidor:9100
18:21:50 nombres registrados ['Pyro.NameServer', 'sd.castro-osorio.juegos']
```


¿Qué partes de la URI reconocen? (protocolo, identificador del objeto, nodo, puerto)

La URI `PYRO:juegos@servidor:9100` tiene cuatro partes:

| Parte | Valor | Significado |
|---|---|---|
| Protocolo | `PYRO` | Protocolo de Pyro5 (también existe `PYROSEC` para TLS) |
| Identificador del objeto | `juegos` | El `objectId` con que el daemon registró la clase `Juegos` |
| Nodo | `servidor` | Nombre del contenedor donde vive el daemon. No es `localhost` porque el cliente corre en otro contenedor |
| Puerto | `9100` | Puerto fijo del daemon (`SERVIDOR_PUERTO`) |

El nombre lógico `sd.castro-osorio.juegos` es lo que el servidor de nombres
traduce a esa URI. El cliente usa el nombre y no necesita saber dónde está el servidor.


## Paso 2, su dominio como objeto remoto

Operaciones que expusieron y en qué clase quedó cada una

| Clase | Método | ¿Cambia estado? |
|---|---|---|
| `Juegos` (entrada, con nombre) | `tabla()` | No, consulta la tabla de puntajes |
| `Juegos` | `unir(jugador)` | Sí, agrega un jugador con 0 puntos en `dominio.py` |
| `Juegos` | `anotar(jugador, puntos)` | Sí, suma puntos en `dominio.py` |
| `Juegos` | `quien_soy()` | No cambia el dominio (solo el contador de llamadas de la instancia) |
| `Juegos` | `partidas_vivas()` | No, cuenta las `Partida` registradas en el daemon |
| `Juegos` | `abrir_partida(jugador)` | Sí, crea una `Partida` y la registra en el daemon (fábrica) |
| `Partida` (con estado, por referencia) | `sumar(puntos)` | Sí, acumula puntos en la partida, no toca la tabla |
| `Partida` | `ver()` | No, devuelve una copia (por valor) del estado |
| `Partida` | `finalizar()` | Sí, aplica los puntos a la tabla y desregistra la partida |
| `Partida` | `cancelar()` | Sí, desregistra la partida sin tocar la tabla |

Todos los métodos solo delegan en `dominio.py`, que es el mismo de la semana 11.
`Juegos` es el único objeto con nombre en el servidor de nombres. `Partida` no tiene
nombre, el cliente la recibe como referencia desde `abrir_partida`.

## Paso 3, paso por referencia

Referencia que recibió el cliente al abrir el objeto con estado (`partida`)

```
18:28:29 recibí Proxy, referencia PYRO:obj_0b9538c8915249f3887ba0b1ec41f893@servidor:9100
18:28:29 estado en el servidor {'jugador': 'david', 'puntos': 5}
18:28:29 finalizar -> {'jugador': 'david', 'puntos': 5}
18:28:29 uso la referencia después de finalizar
18:28:29 ERROR del daemon. La referencia apunta a un objeto que ya no existe. unknown object
```

El cliente no recibe una copia de `Partida`, recibe un `Proxy`. El estado (los puntos)
sigue viviendo en el servidor y cada llamada (`sumar`, `ver`, `finalizar`) viaja por la
red hasta ese objeto. La URI `PYRO:obj_...@servidor:9100` lo identifica. El id lo genera
Pyro5 al hacer `register(partida)`, a diferencia del objeto de entrada, que se publica
con el id fijo `juegos` y un nombre en el servidor de nombres.

¿Qué pasó con `POR_VALOR=1`? ¿Por qué el cliente rechaza el objeto?

```
18:30:09 ERROR de serialización. El servidor intentó enviar un objeto por valor. unsupported serialized class: objetos.Partida
```

Con `POR_VALOR=1`, `abrir_partida` devuelve la `Partida` sin registrarla en el daemon.
Pyro5 solo puede entregar un Proxy si el objeto está registrado, así que intenta
enviarlo serializado (por valor). El cliente recibe un diccionario que dice ser de la
clase `objetos.Partida`, pero no tiene esa clase para reconstruirla y la rechaza con
`unsupported serialized class`. Con `POR_VALOR=0` el objeto se registra y viaja como
referencia, que es lo que permite que el estado siga en el servidor.

¿Qué pasó al usar la referencia después de confirmar?

Después de `finalizar()` la partida se desregistró del daemon (`unregister`). El servidor
sigue vivo y responde, pero ya no existe ningún objeto con esa URI, así que `ver()` falla
con `unknown object`. Es una referencia colgante: el cliente conserva la URI pero el
objeto ya terminó su vida. Pyro5 no avisa a los clientes cuando esto ocurre, por eso el
ciclo de vida (quién crea, quién termina) hay que definirlo en el diseño.

## Paso 4, modo de instancia

| Modo | Instancia del proxy A | Instancia del proxy B | ¿Comparten el contador? |
|---|---|---|---|
| single | | | |
| session | | | |

¿En cuál de los dos modos guardarían estado de un cliente? ¿Por qué el stock no cambia entre modos?

## Paso 5, falla en tres tiempos

| Tiempo | Qué hicimos | Qué vio `vigilar` | Qué vio un cliente nuevo | Qué pasó con el estado |
|---|---|---|---|---|
| 1. servidor muerto | | | | |
| 2. servidor vuelve | | | | |
| 3. nombres muerto y de vuelta | | | | |

¿Qué nodo es punto único de falla en esta arquitectura? ¿Cómo lo resolverían?
