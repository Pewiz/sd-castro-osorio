# Semana 9 — Comunicación y serialización explícita

Sistemas Distribuidos (FDICI25) · Universidad de Los Lagos · 22 y 23 de octubre de 2026

## Carpetas

| Carpeta | Para quién | Qué contiene |
|---|---|---|
| `demo/` | Jueves, lo corre el docente | Demo 1 (cliente contra servidor pausado y detenido) y demo 2 (`serializar.py`, un mismo mensaje en texto, JSON, XML, struct y Protobuf) |
| `laboratorio/` | Viernes, cada equipo | Plantilla que el equipo copia sobre su `semana09/` (`mensajes.py`, `codec.py`, `bench_codec.py`, `servidor.py`, `cliente.py`, `cliente_malo.py`, `docker-compose.yml`, `protocolo.md` v3, `observaciones.md`) |

## Cómo parte el laboratorio

```bash
# en el repositorio del equipo
cp -r semana07 semana09
cp /ruta/al/zip/laboratorio/*.py /ruta/al/zip/laboratorio/*.md semana09/
# comparen el docker-compose.yml del ZIP con el suyo y agreguen la variable CODEC
cd semana09
docker compose up -d servidor cliente
docker compose exec cliente python cliente.py HOLA
```

Alias recomendado para la sesión: `alias c='docker compose exec cliente'` (bash/zsh) o `function c { docker compose exec cliente @args }` (PowerShell).

## Variables

| Variable | Servicio | Valores | Para qué |
|---|---|---|---|
| `CODEC` | servidor y cliente | `json` (defecto), `bin` | Formato del cuerpo del mensaje. Debe coincidir en ambos lados |
| `TIMEOUT_CLIENTE` | cliente | segundos, defecto 5 | Cuánto espera el cliente una respuesta |
| `TIMEOUT_SERVIDOR` | servidor | segundos, defecto 30 | Cuánto espera el servidor un mensaje completo antes de cerrar la conexión |
| `SERVIDOR_HOST`, `SERVIDOR_PUERTO` | cliente | `servidor`, `5000` | Dónde está el servidor dentro de `sd_net` |

## Entrega (viernes 23-10, antes de las 16.00 en el repo del equipo)

- `semana09/` completo con `protocolo.md` v3 y `observaciones.md` con la tabla de medición y el registro de las fallas.
- Commit y push. El trabajo autónomo de la semana 10 está en la guía aparte.
