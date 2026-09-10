# Análisis de caso: BitTorrent

**Equipo:** David Osorio / Felipe Castro  ·  **Fecha:** 04-09-2026

## 1. Modelo dominante

**P2P**

Justificación con las preguntas de la matriz (marcar la que más pesó):

- **¿Quién manda?** **[esta pesó más]** Nadie manda el enjambre. El tracker (o la DHT) responde “quién tiene qué”. Cada peer elige a quién hablar (tit-for-tat) y qué trozo pedir (rarest-first).
- **¿Los nodos son parecidos?** Sí en rol: leecher y seeder son el mismo programa; quien descarga también sube. Difieren en cuánto archivo tienen y en ancho de banda.
- **¿Qué tan lejos están?** En Internet, en cualquier red.
- **¿Qué pasa si uno desaparece?** El resto sigue. Entrar y salir es lo normal (churn). Un peer menos baja capacidad; en el peor caso deja un trozo sin copias.

Modelos secundarios:

- **Tracker:** directorio de peers. Los bytes van de peer a peer.
- **Web:** entrega el `.torrent` o el magnet para arrancar el swarm.

## 2. Nodos y roles

| Nodo | Rol | ¿Cuántos? | ¿Estado o sin estado? |
|---|---|---|---|
| Tracker (HTTP/UDP) | Dice quién está en el swarm (`announce` / `scrape`). | 1 (o pocos) por torrent | **Con estado:** lista de peers. Sin el archivo. |
| Leecher | Pide trozos que le faltan y sirve los que ya tiene. | Muchos | **Con estado:** bitfield, trozos, a quién chokea. |
| Seeder | Peer con el archivo completo; solo sube. | 1…N; puede llegar a 0 | **Con estado:** archivo completo. |
| Nodo DHT (Kademlia) | Tracker distribuido: `get_peers` / `announce_peer`. | Muchos | **Con estado:** ruteo y anuncios por infohash. |
| Metainfo (`.torrent` / magnet) | Infohash, hashes SHA-1 de cada trozo, URL del tracker. | 1 por archivo | Dato, no proceso. |

## 3. Diagrama de interacciones

```
                    .torrent / magnet
                    (infohash, hashes de trozos, URL tracker)
  [Web] ---------------------------------------------------> [Leecher A]
                                                                  |
                       announce (HTTP GET o UDP)                  |
                       "estoy en IP:puerto, infohash X"           |
                                                                  v
                                                           [Tracker]
                                                                  |
                       compact peer list                          |
                       "habla con B, C y el Seeder"               |
                                                                  v
  [Leecher B] <======== protocolo BitTorrent (TCP o uTP) =======> [Leecher A]
       ^     handshake, bitfield, interested, unchoke,            |
       |     request, piece, have, choke                          |
       |                                                          v
       +======================= piece / have ==================> [Seeder]

  Si el tracker no responde, el mismo infohash va a la DHT:

  [Leecher A] -- ping / find_node / get_peers / announce_peer --> [nodos DHT]
```

Entre peers:

1. **handshake** + **bitfield** — quién soy y qué trozos tengo.
2. **interested** / **unchoke** — tit-for-tat (con *optimistic unchoke* para peers nuevos).
3. **request** / **piece** — se piden bloques; el trozo se verifica con el SHA-1 del metainfo.
4. **have** — “ya tengo el trozo k”; el resto actualiza rareza (rarest-first).

| Pregunta | Respuesta |
|---|---|
| ¿Quién decide qué trozo se pide primero? | El propio leecher: **rarest-first**. Al inicio, un trozo al azar; al final, *endgame*. |
| ¿Cómo sabe que el trozo no está corrupto? | SHA-1 en el metainfo. Si no calza, se descarta y se pide de nuevo. |
| ¿Qué pasa cuando el último seeder se va? | Sección 5. |

## 4. Desafío dominante

**Tolerancia a fallos** (churn: nodos que entran y salen sin aviso).

**Cómo lo resuelve el sistema**

- El archivo está **partido y replicado**: perder un peer no borra el objeto entero.
- **Rarest-first** copia primero lo escaso, para que un seeder que se va deje menos trozos únicos.
- **Hashes por trozo:** un `piece` corrupto o falso se descarta.
- **DHT** si cae el tracker: el descubrimiento no depende de una sola máquina.
- **Tit-for-tat + optimistic unchoke:** el swarm sigue encontrando quién sí sube.

**Falacia que estaríamos asumiendo si no lo hiciera**

**“La topología no cambia”.** Si el enjambre fuera un grafo fijo, no haría falta tracker periódico, DHT, bitfield ni rarest-first. También **“la red es fiable”**: sin SHA-1 se aceptaría basura como si el `piece` hubiera llegado bien.

## 5. ¿Qué pasa si cae X?

**X = el último seeder.**

- **Qué siguen viendo los usuarios:** el cliente sigue en el swarm. Pueden intercambiar trozos que ya están entre leechers. La barra no se va a cero.
- **Qué deja de funcionar:** completar el archivo **si algún trozo solo lo tenía ese seeder**. Quedan todos en el mismo porcentaje pidiendo un trozo que nadie tiene. Si todos los trozos ya estaban en al menos un leecher, el swarm puede terminar sin seeders.
- **¿AP o CP?** **AP.** El cliente sigue sirviendo y pidiendo. La vista de “quién tiene qué” puede estar vieja (lista del tracker, nodos DHT muertos). Lo estricto es la **integridad del trozo** (hash). Cómo se sabe: `announce` falla o timeout; el seeder deja de responder; el trozo raro nunca llega.

## 6. La desventaja que vamos a defender

**Nadie garantiza que el objeto completo siga existiendo.** El archivo vive en los peers; el 100 % depende de que alguien se quede de seeder.

**Ejemplo:** el PDF de un ramo se comparte por torrent. El día del certamen hay 30 leechers y 1 seeder (el ayudante). Si el ayudante cierra el notebook y el trozo 47 solo estaba en su disco, los 30 clientes quedan en 98 %: el tracker sigue dando IPs, el protocolo sigue, y **no hay archivo**.

Rarest-first reduce esa probabilidad; no la elimina.
