# Guion de la demostración, Evaluación 3 (viernes 16-10)

> Equipo Castro - Osorio, dominio Juegos (tabla de puntajes).
> Tiempo total 9 minutos de demostración más 3 de preguntas.

| Minuto | Qué mostramos | Quién habla | Comando o archivo en pantalla |
|---|---|---|---|
| 0 a 2 | Arquitectura, diagrama de despliegue y qué capa vive en qué nivel | David | `diagramas/despliegue_v2.png` |
| 2 a 4 | Protocolo, dos operaciones correctas y un error documentado | David | `interfaz_http.md` y `c python cliente_http.py GET /jugadores`, `POST /jugadores jugador=ana`, `POST /jugadores jugador=ana` (409) |
| 4 a 5 | Topología de contenedores levantada desde cero | Felipe | `docker compose up -d` y `docker compose ps` |
| 5 a 6 | Varios clientes a la vez y estado compartido correcto | Felipe | `c python cliente_http.py --repetir 100 --paralelo 10 POST /jugadores/felipe/puntos puntos=1` |
| 6 a 9 | Falla provocada, predicción, ejecución y explicación | Felipe y David | `docker compose kill api1`, luego `docker compose kill servidor` |

## Falla que vamos a provocar

Qué componente cae. Primero `api1` y después el `servidor`.

Qué predecimos que pasa ANTES de ejecutar. Sin api1 todo sigue respondiendo 200 desde api2, una petición tarda cerca de 1 s. Sin servidor la API responde 503 y al levantarlo la tabla vuelve a `david:0 felipe:0`.

Qué pasó en el ensayo. Se cumplió. Sin api1 respondió api2 (una petición en 1.00 s). Sin servidor respondió 503 `SERVIDOR_NO_DISPONIBLE` y al volver se perdieron los puntajes.

Qué haríamos para que el sistema lo tolere mejor. Guardar los puntajes en un volumen o base de datos, para no perderlos al reiniciar el servidor.

## Plan B si algo no levanta

Sin Docker, como en la lámina 14. Terminal 1 `python servidor.py`, terminal 2 `uvicorn api:app --port 8000` con `SERVIDOR_HOST=127.0.0.1`, terminal 3 `python cliente_http.py` con `API_URL=http://127.0.0.1:8000`. Si tampoco funciona, mostramos el diagrama y las salidas del ensayo.
