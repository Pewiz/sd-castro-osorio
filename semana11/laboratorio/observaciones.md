# Observaciones semana 11 · Migración a gRPC

Equipo Castro - Osorio · Dominio Juegos (tabla de puntajes) · Fecha 08-11-2026

## 1. Contrato
- Archivo `proto/servicio.proto` con 3 operaciones: `Tabla`, `Unir` y `Anotar`.
- Operaciones que modifican estado y llevan `id_solicitud`: `Unir` y `Anotar`.
- Operaciones idempotentes (se pueden repetir sin efecto extra): `Tabla`, porque solo lee. `Anotar` no es idempotente, porque suma los puntos cada vez. `Unir` repetida no suma nada, pero la segunda vez da error (`el jugador ya existe`).

## 2. Stubs generados
- Clase del stub en el cliente: `PartidaStub`.
- Clase base del servidor: `PartidaServicer`.
- Qué hace el stub cuando llamamos `stub.Anotar(...)`: convierte la solicitud en bytes (marshalling) y la manda al servidor por la red. Espera la respuesta, la convierte de vuelta en un objeto y la devuelve, o lanza un error si algo falló. Nosotros la usamos como si fuera una función normal.

## 3. Equivalencia de errores JSON-RPC → gRPC

| Caso | JSON-RPC (semana 10) | gRPC (hoy) | Comando usado |
|---|---|---|---|
| Método inexistente | -32601 | UNIMPLEMENTED | `grpc.insecure_channel('servidor:50051').unary_unary('/partida.v1.Partida/Borrar')(b'', timeout=2)` |
| Parámetros inválidos | -32602 | INVALID_ARGUMENT | `cliente_grpc.py anotar felipe 0` |
| Error del dominio | -32000 | FAILED_PRECONDITION | `cliente_grpc.py anotar zzz 5` (el jugador no existe) |
| Servidor caído | sin conexión | UNAVAILABLE | `docker compose stop servidor` y `cliente_grpc.py tabla --timeout 8` |
| Respuesta lenta | timeout del cliente | DEADLINE_EXCEEDED | `FALLA=siempre` y `cliente_grpc.py anotar felipe 25` |

Lo que vimos en cada caso:
- UNIMPLEMENTED: `status = StatusCode.UNIMPLEMENTED, details = "Method not found!"`.
- INVALID_ARGUMENT: `los puntos deben ser mayores que cero`.
- FAILED_PRECONDITION: `el jugador zzz no existe`.
- UNAVAILABLE: con el timeout normal de 2 s, con el servidor detenido, el cliente dio `DEADLINE_EXCEEDED` y no `UNAVAILABLE`. Con `--timeout 8` sí salió `UNAVAILABLE, ... Domain name not found`. Creemos que, con el contenedor detenido, el cliente tarda más de 2 s en darse cuenta de que el servidor no existe.

## 4. Falla intermedia · semántica teórica frente a la observada

| # | Configuración | Qué vio el cliente | Puntos de felipe con `tabla` | Semántica observada |
|---|---|---|---|---|
| 1 | `FALLA=no`, sin reintentos | `OK felipe puntos=25` | 25 | Funciona bien, no hay falla |
| 2 | `FALLA=siempre`, sin reintentos | `DEADLINE_EXCEEDED`, "quedó en estado DESCONOCIDO" | 25 | Maybe: el cliente cree que falló, pero se aplicó una vez |
| 3 | `FALLA=siempre`, `--reintentos 2`, sin `DEDUP` | `DEADLINE_EXCEEDED` en los 3 intentos, "estado DESCONOCIDO" | 75 | At-least-once: se aplicó 3 veces |
| 4 | `FALLA=siempre DEDUP=1`, `--reintentos 2` | Intento 1 `DEADLINE_EXCEEDED`, intento 2 `OK felipe puntos=25` | 25 | At-most-once: se aplicó 1 vez |
| 5 | `docker compose kill servidor` durante una llamada | `UNAVAILABLE, Socket closed`, "estado DESCONOCIDO" | 0 después de reiniciar (volvió al estado inicial) | El servidor aplicó el cambio, pero se perdió al morir el proceso |

Líneas de `docker compose logs servidor` de los casos 3 y 4:

```
# caso 3, sin DEDUP
[servidor] Anotar id=4ba56b26 -> {'jugador': 'felipe', 'puntos': 25}
[servidor] FALLA=siempre, cambio YA aplicado, demoro la respuesta 3 s
[servidor] Anotar id=4ba56b26 -> {'jugador': 'felipe', 'puntos': 50}
[servidor] FALLA=siempre, cambio YA aplicado, demoro la respuesta 3 s
[servidor] Anotar id=4ba56b26 -> {'jugador': 'felipe', 'puntos': 75}
[servidor] FALLA=siempre, cambio YA aplicado, demoro la respuesta 3 s

# caso 4, con DEDUP=1
[servidor] Anotar id=c77c5d9e -> {'jugador': 'felipe', 'puntos': 25}
[servidor] FALLA=siempre, cambio YA aplicado, demoro la respuesta 3 s
[servidor] Anotar id=c77c5d9e repetido, devuelvo lo guardado SIN aplicar de nuevo
```

Lo que notamos: en el caso 3 el cliente vio 3 errores, pero el servidor hizo el trabajo 3 veces. El número de errores que ve el cliente no dice cuántas veces se hizo el trabajo. En el caso 5, el servidor guardaba el estado solo en memoria, así que al morir se perdió todo y el cliente nunca supo si se había aplicado.

## 5. Conclusión
Las operaciones que suman, como `Anotar`, serían peligrosas de reintentar sin `id_solicitud`: si el cliente reintenta, el jugador recibe puntos de más (como pasó en el caso 3, donde 25 puntos pasaron a ser 75). En un juego real eso significaría puntajes falsos en la tabla, y en una competencia, un ganador equivocado. `Tabla` se puede reintentar sin problema porque solo lee.
