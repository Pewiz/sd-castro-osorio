# Semana 13, colas de mensajes y master-worker

Todo lo de la semana 12 sigue igual (`nombres`, `servidor`, `cliente` con Pyro5). Lo nuevo
es un broker RabbitMQ y cuatro programas que hablan con él por AMQP (TCP 5672) dentro de
`sd_net`. El publicador y el master no llaman a nadie directamente, dejan mensajes en una
cola y siguen.

| Archivo | Qué es |
|---|---|
| `dominio.py`, `objetos.py`, `servidor_pyro.py`, `cliente_pyro.py` | Los de la semana 12, sin cambios |
| `cola.py` (nuevo) | Lo común: conexión con reintentos, nombres de colas, publicar persistente |
| `publicador.py` (nuevo) | Deja operaciones del dominio (`TABLA`, `UNIR`, `ANOTAR`) en la cola `operaciones` |
| `procesador.py` (nuevo) | Consume `operaciones` con ack manual y `prefetch=1`. Descarta los mensajes venenosos |
| `master.py` (nuevo) | Parte [2, 5 000 000) en 40 trozos, junta los resultados, valida y escribe el CSV |
| `worker.py` (nuevo) | Cuenta los primos de un trozo. Sin estado, se escala con `--scale` |
| `graficar.py` (nuevo) | Tabla de T(p), S(p), E(p) y Karp-Flatt, y el gráfico `speedup.svg` |
| `Dockerfile.colas` (nuevo) | Imagen con `pika` para los programas de colas |
| `docker-compose.yml` | Se agregan `rabbitmq`, `procesador`, `worker`, `publicador`, `master` y `graficar` |
| `.env` | Configuración (`EQUIPO`, `AUTO_ACK`, `DEMORA` y las de la semana 12). Es un archivo oculto |
| `observaciones_semana13.md` | Registro del taller con las salidas reales |
| `analisis_speedup.md` | Trabajo autónomo. Por qué el speedup no es lineal, tres causas y dos experimentos propios |
| `mediciones/` | `mediciones.csv` y `speedup.svg` del taller. `experimento_workers.*` y `experimento_trozos.csv` del análisis |

## Colas

| Cola | Quién publica | Quién consume | Para qué |
|---|---|---|---|
| `operaciones` | `publicador` | `procesador` (1 a 3 réplicas) | Operaciones del dominio, pasos 2 y 3 |
| `tareas_primos` | `master` | `worker` (1 a 4 réplicas) | Trozos del rango a revisar, paso 4 |
| `resultados_primos` | `worker` | `master` | Un resultado por trozo, paso 4 |

Las tres son durables y todos los mensajes son persistentes (`delivery_mode=2`).

## Levantar y probar

```bash
docker compose up -d rabbitmq procesador
docker compose run --rm publicador ANOTAR david 5
docker compose logs procesador
```

Consola web en `http://localhost:15672`, usuario y clave `guest`, pestaña Queues.

Master-worker y speedup

```bash
docker compose stop procesador
docker compose up -d --scale worker=2 worker
docker compose run --rm master
docker compose run --rm graficar
```

`publicador`, `master` y `graficar` están en el perfil `herramientas`, por eso `docker compose up -d`
no los levanta. Se ejecutan con `docker compose run --rm` y terminan solos. Por la misma razón,
`docker compose build` no los reconstruye. Si cambian el código usen `docker compose --profile herramientas build`.

Experimentos sin mezclar con las mediciones del taller

```bash
docker compose run --rm master --trozos 120 --csv mediciones/experimento_workers.csv
docker compose run --rm graficar --trozos 120 --csv mediciones/experimento_workers.csv --svg mediciones/experimento_workers.svg
```

## Variables

| Variable | Valor por defecto | Para qué |
|---|---|---|
| `AUTO_ACK` | `0` | Con `1` el procesador confirma al recibir (at-most-once, experimento del paso 3) |
| `DEMORA` | `3` | Segundos que el procesador tarda en "procesar" cada operación |
| `N` | `5000000` | Fin del rango del master (también `--n`) |
| `TROZOS` | `40` | Cuántos trozos publica el master (también `--trozos`) |
| `RABBIT_HOST` | `rabbitmq` | Dónde está el broker |

Igual que en la semana 12, los valores se cambian en `.env` (por ejemplo `AUTO_ACK=1`) y después
`docker compose up -d --scale procesador=3 procesador`.

El compose tiene `name: semana13`, así las réplicas se llaman `semana13-procesador-2`,
`semana13-worker-1`, etc. Con `docker compose ps` se ve el nombre exacto antes de un `docker kill`.

## Limpieza

```bash
docker compose down -v
```
