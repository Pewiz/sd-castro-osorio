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

```
--- MODO=single
20:45:54 proxy A -> {'modo': 'single', 'instancia': 1, 'llamadas': 1, 'cliente': "('172.22.0.4', 32832)"}
20:45:54 proxy A -> {'modo': 'single', 'instancia': 1, 'llamadas': 2, 'cliente': "('172.22.0.4', 32832)"}
20:45:54 proxy A -> {'modo': 'single', 'instancia': 1, 'llamadas': 3, 'cliente': "('172.22.0.4', 32832)"}
20:45:54 proxy B -> {'modo': 'single', 'instancia': 1, 'llamadas': 4, 'cliente': "('172.22.0.4', 32848)"}
20:45:54 proxy B -> {'modo': 'single', 'instancia': 1, 'llamadas': 5, 'cliente': "('172.22.0.4', 32848)"}
20:45:54 proxy B -> {'modo': 'single', 'instancia': 1, 'llamadas': 6, 'cliente': "('172.22.0.4', 32848)"}
--- MODO=session
20:46:17 proxy A -> {'modo': 'session', 'instancia': 1, 'llamadas': 1, 'cliente': "('172.22.0.4', 39836)"}
20:46:17 proxy A -> {'modo': 'session', 'instancia': 1, 'llamadas': 2, 'cliente': "('172.22.0.4', 39836)"}
20:46:17 proxy A -> {'modo': 'session', 'instancia': 1, 'llamadas': 3, 'cliente': "('172.22.0.4', 39836)"}
20:46:17 proxy B -> {'modo': 'session', 'instancia': 2, 'llamadas': 1, 'cliente': "('172.22.0.4', 39840)"}
20:46:17 proxy B -> {'modo': 'session', 'instancia': 2, 'llamadas': 2, 'cliente': "('172.22.0.4', 39840)"}
20:46:17 proxy B -> {'modo': 'session', 'instancia': 2, 'llamadas': 3, 'cliente': "('172.22.0.4', 39840)"}
20:46:17 anotar -> {'jugador': 'david', 'puntos': 4}
20:46:18 tabla {'david': 4, 'felipe': 0}
```

| Modo | Instancia del proxy A | Instancia del proxy B | ¿Comparten el contador? |
|---|---|---|---|
| single | 1 | 1 | Sí. El proxy B sigue contando desde 4, es el mismo objeto `Juegos` para todos |
| session | 1 | 2 | No. Cada proxy (cada conexión) tiene su propia instancia y cuenta desde 1 |

¿En cuál de los dos modos guardarían estado de un cliente? ¿Por qué el stock no cambia entre modos?

En `session`, porque cada proxy recibe su propia instancia y lo que guarde un cliente no
lo ve ni lo pisa otro. En `single` todos los clientes comparten el mismo objeto, como pasa
con el contador `llamadas`. Ese estado dura lo que dura la conexión del proxy, si el proxy
se cierra o se cae la conexión, la instancia se pierde.

La tabla (nuestro "stock") no cambia entre modos porque no vive en la instancia de `Juegos`,
vive en `_puntajes` dentro de `dominio.py`, que es uno solo por proceso. Todas las instancias
delegan en el mismo módulo. Se ve en la prueba: `anotar david 4` y `tabla` se ejecutaron con
proxies distintos (instancias distintas en `session`) y la tabla mostró los 4 puntos.

## Paso 5, falla en tres tiempos

Antes de la falla agregamos estado con `unir ana` y `anotar ana 10`. En la terminal 2 quedó
corriendo `vigilar` y en la terminal 3 `partida david 5 --esperar 20`.

```
# terminal 2, vigilar
20:46:52 ok, tabla {'david': 0, 'felipe': 0, 'ana': 10}  [PYRONAME:sd.castro-osorio.juegos@nombres:9090]
20:46:53 FALLA de comunicación ConnectionClosedError receiving: not enough data
20:47:00 no pude reconectar ConnectionClosedError
20:47:13 FALLA de comunicación CommunicationError cannot connect to ('servidor', 9100): [Errno -2] Name or service not known
20:47:13 reconectado
20:47:14 ok, tabla {'david': 0, 'felipe': 0}  [PYRONAME:sd.castro-osorio.juegos@nombres:9090]

# terminal 3, partida
20:46:48 recibí Proxy, referencia PYRO:obj_bded720f58534270aef73dfb45b9df13@servidor:9100
20:46:48 estado en el servidor {'jugador': 'david', 'puntos': 5}
20:46:48 espero 20 s antes de finalizar (momento para la falla)
20:47:09 se cortó la conexión (ConnectionClosedError). Reintento con la MISMA referencia durante 30 s, levanten el servidor
20:47:13 ERROR. El servidor responde, pero el objeto de esa referencia ya no existe (referencia colgante). connection to ('servidor', 9100) rejected: unknown object

# cliente nuevo con el servidor muerto
20:47:06 ERROR de comunicación. CommunicationError cannot connect to ('servidor', 9100): [Errno -2] Name or service not known

# cliente nuevo con el servidor de vuelta
20:47:16 tabla {'david': 0, 'felipe': 0}
20:47:17 partidas vivas en el servidor 0
```

Para el tiempo 3 dejamos `vigilar` corriendo y antes anotamos `anotar felipe 7`.

```
# cliente nuevo con nombres muerto
20:48:06 ERROR de nombres. No encuentro sd.castro-osorio.juegos. Failed to locate the nameserver

# cliente nuevo con nombres de vuelta (también falla uri)
20:48:13 ERROR de nombres. No encuentro sd.castro-osorio.juegos. unknown name: sd.castro-osorio.juegos

# vigilar, todo el tiempo que nombres estuvo caído siguió respondiendo
20:48:06 ok, tabla {'david': 0, 'felipe': 7}  [PYRONAME:sd.castro-osorio.juegos@nombres:9090]
20:48:13 ok, tabla {'david': 0, 'felipe': 7}  [PYRONAME:sd.castro-osorio.juegos@nombres:9090]

# docker compose restart servidor (se vuelve a registrar al arrancar)
20:48:25 FALLA de comunicación ConnectionClosedError receiving: not enough data
20:48:25 no pude reconectar NamingError
20:48:26 ok, tabla {'david': 0, 'felipe': 0}  [PYRONAME:sd.castro-osorio.juegos@nombres:9090]
20:48:29 tabla {'david': 0, 'felipe': 0}
```

| Tiempo | Qué hicimos | Qué vio `vigilar` | Qué vio un cliente nuevo | Qué pasó con el estado |
|---|---|---|---|---|
| 1. servidor muerto | `docker compose kill servidor` con `vigilar` y una partida esperando | `FALLA de comunicación ConnectionClosedError` y `no pude reconectar` | `ERROR de comunicación ... cannot connect to ('servidor', 9100)`. El servidor de nombres todavía le entregó la URI vieja | La tabla y la partida vivían en la memoria del proceso y murieron con él |
| 2. servidor vuelve | `docker compose start servidor` | `reconectado` y después `ok, tabla {'david': 0, 'felipe': 0}`, sin `ana` | `tabla {'david': 0, 'felipe': 0}` y `partidas vivas 0` | Se perdió `ana` con sus 10 puntos. La partida reintentó con la misma referencia y recibió `unknown object`, los 5 puntos de `david` nunca llegaron a la tabla |
| 3. nombres muerto y de vuelta | `docker compose kill nombres`, `docker compose start nombres` y al final `docker compose restart servidor` | Siguió en `ok` todo el tiempo, ya tenía la conexión directa al daemon. Solo falló durante el reinicio del servidor | Con nombres muerto `Failed to locate the nameserver`. Con nombres de vuelta `unknown name`. Funcionó solo después de reiniciar el servidor | La tabla (`felipe 7`) sobrevivió a la caída de nombres. Se perdió al reiniciar el servidor para que se registrara de nuevo |

¿Qué nodo es punto único de falla en esta arquitectura? ¿Cómo lo resolverían?

Los dos, pero de forma distinta. El `servidor` es punto único de falla del estado: la tabla
y las partidas existen una sola vez y en memoria, si se cae se pierden y las referencias
quedan colgantes. El `nombres` es punto único de falla para encontrar el servicio: los
clientes que ya tienen el proxy siguen funcionando, pero ningún cliente nuevo puede entrar,
y como el registro también vive en memoria, al volver no recuerda a nadie.

Para `nombres`, activar `REREGISTRO`. Lo probamos con `REREGISTRO=5`: matamos y levantamos
`nombres` sin reiniciar el servidor, y a los pocos segundos un cliente nuevo respondió
`tabla {'david': 0, 'felipe': 7}`, sin perder estado. También se puede usar el almacenamiento
persistente del servidor de nombres (`-s sql:archivo`) o tener más de uno. Para el `servidor`,
guardar la tabla fuera de la memoria del proceso (una base de datos o un archivo) y tener
réplicas registradas, así un reinicio no borra los puntajes.
