# Proyecto integrador, servicio de juegos (tabla de puntajes)

Equipo Castro - Osorio · Felipe Castro, David Osorio

Es el mismo dominio de todo el semestre (`dominio.py`: `tabla`, `unir`, `anotar`), expuesto como
objetos remotos con Pyro5 (semana 12). En la semana 13 se agregó una **cola de jugadas**: el juego
deja las jugadas en RabbitMQ y dos procesadores sin estado las aplican en el servidor real.

La topología está en `topologia_colas.drawio` (se abre en app.diagrams.net).

## Levantar en tres comandos

```bash
docker compose up -d --build
docker compose run --rm publicador ANOTAR david 5
docker compose exec cliente python cliente_pyro.py tabla
```

Consola de RabbitMQ en `http://localhost:15672` (usuario y clave `guest`).

Si cambian el código, reconstruyan también el publicador con `docker compose --profile herramientas build`.
Está en el perfil `herramientas` y `up --build` no lo reconstruye.

Antes de levantarlo, bajen `semana12/laboratorio` y `semana13/laboratorio` con `docker compose down`,
porque usan los mismos nombres de contenedor (`sd_nombres`, `sd_servidor`, `sd_cliente`, `sd_rabbitmq`).

## Nodos

| Nodo (servicio) | Rol | Se comunica con |
|---|---|---|
| `nombres` | Servidor de nombres de Pyro5 | todos los que buscan `sd.castro-osorio.juegos` |
| `servidor` | Daemon Pyro5 con `Juegos` y `Partida`. Único nodo con estado | `nombres` (se registra cada 5 s) |
| `cliente` | Consultas y partidas con `cliente_pyro.py` | `nombres`, `servidor` |
| `rabbitmq` | Broker, cola durable `operaciones` | `publicador`, `procesador` |
| `procesador` (2 réplicas) | Consume la cola y llama a `Juegos.aplicar()` | `rabbitmq`, `nombres`, `servidor` |
| `publicador` | De un solo uso (`run --rm`), deja jugadas en la cola | `rabbitmq` |

## Archivos

| Archivo | Qué es |
|---|---|
| `dominio.py` | Reglas del negocio, sin red. El mismo de las semanas 11 a 13 |
| `objetos.py` | `Juegos` y `Partida` (semana 12) más `Juegos.aplicar()`, que no aplica dos veces el mismo `id_solicitud` |
| `servidor_pyro.py`, `cliente_pyro.py` | Los de la semana 12 |
| `cola.py` | Conexión al broker con reintentos y publicación persistente |
| `publicador.py` | Publica `UNIR` o `ANOTAR` con un `id_solicitud` único por mensaje |
| `procesador.py` | Consume `operaciones`, `prefetch=1`, ack manual. Llama al servidor real |
| `topologia_colas.drawio` | Topología con la cola |
| `ALCANCE.md`, `ENUNCIADO.md`, `bitacora.md` | Documentos del proyecto |

## Cómo trata el procesador cada jugada

| Resultado de `Juegos.aplicar()` | Qué hace con el mensaje | Por qué |
|---|---|---|
| Aplicada | `basic_ack` | El broker la borra recién cuando el servidor la aplicó |
| Repetida (el id ya estaba aplicado) | `basic_ack` sin tocar la tabla | Es una reentrega. Ack + idempotencia da efecto exactly-once |
| Error del dominio (jugador no existe, puntos inválidos) | `basic_reject` sin reencolar | Fallaría siempre, es un mensaje venenoso |
| Servidor o nombres caído | `basic_nack` con reencolar, después de 2 s | La jugada espera en la cola hasta que el servidor vuelva |

`TABLA` no pasa por la cola: quien publica no recibe respuesta, así que las consultas se hacen
directo con `cliente_pyro.py`.

## Fallas probadas (27-11-2026)

1. **Camino normal.** `UNIR ana`, 10 veces `ANOTAR david 1` y `ANOTAR zoe 3`. Las dos réplicas
   se repartieron las jugadas, la tabla quedó en `{'david': 10, 'felipe': 0, 'ana': 0}` y la de
   `zoe` se descartó con `el jugador zoe no existe`.

2. **Muere un procesador después de aplicar y antes del ack.** Con `DEMORA=3` el procesador
   espera 3 s entre aplicar y confirmar.

   ```
   DEMORA=3 docker compose up -d
   docker compose run --rm publicador --n 4 ANOTAR felipe 1
   docker kill proyecto-procesador-1

   procesador-1  | recibido id=ea869411 ANOTAR felipe 1
   procesador-1  | id=ea869411 aplicada en el servidor, espero 3 s antes del ack ...
                    ... docker kill ...
   procesador-2  | recibido id=ea869411 ANOTAR felipe 1 (REENTREGADO)
   procesador-2  | id=ea869411 ya estaba aplicada, el servidor no la repitió
   tabla {'david': 0, 'felipe': 4}
   ```

   Se publicaron 4 jugadas y `felipe` quedó con 4. Sin `aplicar()` habría quedado con 5.

3. **Servidor caído.**

   ```
   docker compose stop servidor
   docker compose run --rm publicador --n 3 ANOTAR david 2
   procesador-1  | servidor no disponible (CommunicationError), id=fad1b425 vuelve a la cola
   docker compose start servidor
   procesador-2  | recibido id=fad1b425 ANOTAR david 2 (REENTREGADO)
   procesador-2  | aplicada id=fad1b425 -> david tiene 6 puntos
   tabla {'david': 6, 'felipe': 0}
   ```

   Ninguna jugada se perdió mientras el servidor estuvo abajo (4 reintentos). Lo que sí se perdió
   fue la tabla anterior, porque vive en memoria. Es la limitación pendiente del proyecto.

## Variables

| Variable | Valor por defecto | Para qué |
|---|---|---|
| `EQUIPO` | `castro-osorio` | Nombre lógico `sd.<EQUIPO>.juegos` |
| `REREGISTRO` | `5` | Segundos entre re-registros en `nombres` (lección de la falla de la semana 12) |
| `DEMORA` | `0` | Segundos entre aplicar en el servidor y el ack, solo para provocar la falla 2 |
| `MODO` | `single` | Modo de instancia de `Juegos` |
