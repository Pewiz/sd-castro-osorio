# Bitácora del proyecto integrador

Una entrada por semana, la más reciente arriba. Cada entrada se sube a más tardar el jueves siguiente a las 18.00.

---

## Entrada 2, semana 13 (27-11-2026)

**Presentes** Felipe Castro, David Osorio

**Qué decidimos**
- Las jugadas que cambian estado (`UNIR`, `ANOTAR`) entran al proyecto por una cola durable de
  RabbitMQ (`operaciones`). El juego las publica y sigue, y dos procesadores sin estado las aplican
  en el servidor real llamando a `Juegos.aplicar()` por Pyro5.
- Las consultas (`tabla`) y las partidas (`Partida`) siguen siendo llamadas directas por Pyro5.
- Cada mensaje lleva un `id_solicitud` y el **servidor** recuerda los ids aplicados, así una
  reentrega no suma dos veces (ack manual + idempotencia).
- Ack recién después de que el servidor responde. Si el servidor no está, `nack` con reencolar.
  Si el dominio rechaza la jugada, `reject` sin reencolar.
- `REREGISTRO=5` por defecto en el servidor, por la falla del servidor de nombres de la semana 12.

**Por qué lo decidimos y qué alternativa descartamos**
- La cola desacopla al juego del servidor en el tiempo: en la prueba, con el servidor detenido, las
  3 jugadas esperaron en la cola y se aplicaron al volver. Con la llamada directa de la semana 12
  esas jugadas se habrían perdido con un `CommunicationError`.
- Descartamos `auto_ack`. En el laboratorio perdimos 4 de 12 mensajes al matar una réplica
  (at-most-once). Con ack manual no se perdió ninguno.
- Descartamos deduplicar en el procesador. Son réplicas sin estado y la reentrega puede llegar a
  la otra réplica, así que la memoria de ids tiene que estar donde vive el estado, en el servidor.
- Descartamos pasar `TABLA` por la cola, porque quien publica no recibe respuesta.
- Dejamos 2 procesadores y no más: el análisis de speedup mostró que pasados los núcleos físicos
  más réplicas no ayudan, y aquí el cuello de botella es el único servidor.

**Qué hicimos**
- Laboratorio completo en `semana13/laboratorio/` (broker, cola durable, reentrega, `auto_ack`,
  master-worker de 1 a 4 workers y gráfico de speedup).
- `semana13/laboratorio/analisis_speedup.md` con dos experimentos propios (1 a 12 workers y 4 a
  4000 trozos) y tres causas con evidencia: núcleos físicos compartidos, comunicación por trozo y
  desbalance.
- Cola integrada en `proyecto/` (`publicador.py`, `procesador.py`, `Juegos.aplicar()`,
  `docker-compose.yml`) y la topología en `proyecto/topologia_colas.drawio`.
- Tres pruebas del proyecto, descritas en `proyecto/README.md`: camino normal, procesador muerto
  entre aplicar y confirmar (la reentrega no duplicó, `felipe` quedó en 4 y no en 5) y servidor
  caído (ninguna jugada perdida).

**Problemas encontrados y cómo los abordamos**
- `docker compose build` no reconstruye los servicios con `profiles`, y el master siguió con el
  código viejo. Se resuelve con `docker compose --profile herramientas build`, y quedó anotado en
  los README.
- El procesador partía antes de que RabbitMQ aceptara conexiones AMQP, aunque el healthcheck ya
  decía `healthy`. `conectar()` reintenta hasta 30 veces y el procesador se conecta solo.
- Con el servidor caído, cada intento demora unos 8 s en fallar (resolver el nombre `servidor`)
  más los 2 s de espera. Funciona, pero hace lenta la recuperación.
- Al volver el servidor, la tabla parte de cero porque vive en memoria. Las jugadas en cola no
  se pierden, pero el estado anterior sí.

**Próximo paso y responsable**

| Tarea | Responsable | Para cuándo |
|---|---|---|
| Guardar la tabla y los ids aplicados fuera de la memoria del servidor (archivo o base de datos) | Equipo | 04-12 |
| Segunda clase de objeto remoto en otro nodo que llame a `Juegos` (requisito 2 del enunciado) | Equipo | 04-12 |
| Completar y subir `ALCANCE.md` con lo aprobado en clase | Equipo | 04-12 |
| Mecanismo de coordinación (semana 16) | Equipo | 11-12 |

---

## Entrada 1, semana 12 (13-11-2026)

**Presentes**

**Qué decidimos**
-

**Por qué lo decidimos y qué alternativa descartamos**
-

**Qué hicimos**
-

**Problemas encontrados y cómo los abordamos**
-

**Próximo paso y responsable**

| Tarea | Responsable | Para cuándo |
|---|---|---|
| | | |
