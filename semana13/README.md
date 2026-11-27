# semana13, colas de mensajes y master-worker con RabbitMQ

| Carpeta | Para qué |
|---|---|
| `laboratorio/` | Taller del viernes 20-11. Es `semana12/laboratorio` más el broker RabbitMQ, la cola de operaciones del dominio y el master-worker de primos |

## Entregas

- `laboratorio/` con `docker-compose.yml` con rabbitmq, `observaciones_semana13.md`,
  `mediciones/mediciones.csv` y `mediciones/speedup.svg`, **viernes 20-11 antes de las 16.00**.
- Trabajo autónomo, **jueves 26-11 a las 18.00**

| Entrega | Dónde quedó |
|---|---|
| Análisis de speedup, tres causas con evidencia y un experimento propio | `laboratorio/analisis_speedup.md` |
| Topología del proyecto con la cola | `proyecto/topologia_colas.drawio` |
| Cola integrada al proyecto, el procesador llama al servidor real | `proyecto/` (`publicador.py`, `procesador.py`, `Juegos.aplicar()` en `objetos.py`) |
| Bitácora del proyecto | `proyecto/bitacora.md`, entrada 2 |

El nombre del equipo se define una sola vez en `laboratorio/.env` (`EQUIPO=castro-osorio`, sin espacios).

Antes de levantar `semana13/`, bajen lo de la semana anterior con `docker compose down` dentro de
`semana12/laboratorio/`, porque los nombres de contenedor `sd_nombres`, `sd_servidor` y `sd_cliente`
se repiten.
