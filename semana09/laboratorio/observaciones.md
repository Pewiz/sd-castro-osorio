# Observaciones — Semana 9, serialización explícita

**Equipo:** Castro - Osorio  **Integrantes:** Felipe Castro, David Osorio  **Fecha:** 23-10-2026

## Paso 2 — Ida y vuelta de los codecs

Salida de `python codec.py`:

```
json  solicitud  78 bytes  b'{"operacion": "ANOTAR", "argumentos": ["felipe", "15"], "id": 7, "version": 2}'
json  respuesta  65 bytes  b'{"id": 7, "estado": "OK", "datos": ["felipe", "15"], "error": ""}'
bin   solicitud  26 bytes  b'\x02\x00\x00\x00\x07\x00\x06ANOTAR\x02\x00\x06felipe\x00\x0215'
bin   respuesta  20 bytes  b'\x00\x00\x00\x07\x00\x02\x00\x06felipe\x00\x0215\x00\x00'
ida y vuelta OK en los dos codecs
```

Tamaño de la misma solicitud en JSON 78 bytes y en bin 26 bytes.

## Paso 3 — Medición

Salida de `python bench_codec.py 10000` (datos del dominio JUEGOS):

```
| Mensaje   | Codec | Bytes promedio | Bytes totales | Codificar (ms) | Decodificar (ms) |
|-----------|-------|---------------:|--------------:|---------------:|-----------------:|
| Solicitud | json  |           73.3 |        733186 |           41.7 |             20.5 |
| Solicitud | bin   |           19.8 |        197534 |            8.6 |             11.4 |
| Respuesta | json  |          102.4 |       1024304 |           44.1 |             21.2 |
| Respuesta | bin   |           50.5 |        505414 |           13.1 |             16.2 |

Solicitud: el binario ocupa 73% menos bytes que JSON
Respuesta: el binario ocupa 51% menos bytes que JSON
```

Conclusión: el binario ocupa mucho menos: 73 % menos en la solicitud y 51 % menos en la respuesta. También es más rápido en codificar y decodificar. Lo malo es que no se puede leer a simple vista, y cliente y servidor tienen que usar el mismo codec.

La respuesta ahorra menos porque casi todo lo que lleva son textos (los nombres y puntajes), y esos ocupan lo mismo en los dos formatos. Lo que se ahorra el binario son las llaves, comillas y nombres de campo, y eso pesa más en la solicitud, que es más corta.

## Paso 4 — Integración

| Prueba | codec=json | codec=bin |
|---|---|---|
| `HOLA felipe` | OK HOLA felipe | OK HOLA felipe |
| `UNIR ana` | OK ana \| 0 | OK ana \| 0 |
| `ANOTAR ana 15` (luego `ANOTAR ana 7`) | OK ana \| 15, luego OK ana \| 22 | OK ana \| 15, luego OK ana \| 22 |
| `TABLA` | OK ana:22 \| david:0 \| felipe:0 | OK ana:22 \| david:0 \| felipe:0 |
| Error del dominio: `ANOTAR zzz 5` | ERROR JUGADOR_NO_EXISTE | ERROR JUGADOR_NO_EXISTE |
| Error del dominio: `UNIR ana` repetido | ERROR JUGADOR_YA_EXISTE | ERROR JUGADOR_YA_EXISTE |

El log del servidor muestra `codec=json` o `codec=bin` según el modo. Los resultados son iguales en los dos; solo cambian los bytes. También probamos la API HTTP con `CODEC=bin` (`GET /jugadores` y `POST /jugadores/felipe/puntos` por `localhost:8080`) y respondió bien.

## Paso 5 — Falla provocada

| Modo de `cliente_malo.py` | Qué vio el cliente | Qué dice el log del servidor | ¿El servidor siguió atendiendo? |
|---|---|---|---|
| `version` | `ERROR versión 1 no soportada, use 2` (igual en json y bin) | `versión no soportada 1 desde ...` | Sí. La conexión sigue abierta y el `HOLA` siguiente respondió OK |
| `largo` | Sin respuesta en 5 s (timeout del cliente) | Solo `conectado` y `desconectado`, nunca hubo solicitud (el servidor seguía esperando los 50 bytes que faltaban) | Sí |
| `basura` (codec json) | `ERROR mensaje mal formado (UnicodeDecodeError)` en 3 de 3 corridas | `UnicodeDecodeError 'utf-8' codec can't decode byte 0xde in position 0: invalid continuation byte` | Sí |
| `basura` (codec bin) | `ERROR mensaje mal formado (UnicodeDecodeError)` en 5 de 5 corridas | `UnicodeDecodeError 'utf-8' codec can't decode byte 0xb8 in position 0: invalid start byte` | Sí |
| `cruzado` (cliente json → servidor bin) | `ERROR mensaje mal formado (struct.error)` | `struct.error unpack_from requires a buffer of at least 29289 bytes ... (actual buffer size is 78)` | Sí |
| `cruzado` (cliente bin → servidor json) | `ERROR mensaje mal formado (JSONDecodeError)` | `JSONDecodeError Expecting value: line 1 column 1 (char 0)` | Sí |

Después de cada falla, `cliente.py HOLA` respondió OK. El servidor solo cierra la conexión que falló.

¿Cuál de los dos codecs falló de forma más clara ante la basura y por qué?

En nuestras pruebas los dos codecs fallaron igual de claro, con `UnicodeDecodeError`. Aun así, creemos que JSON falla mejor: los bytes al azar casi nunca forman un JSON válido, así que siempre da error. En binario cualquier secuencia de bytes se puede interpretar de alguna forma, y con otros bytes al azar podría pasar como un mensaje válido sin que nos demos cuenta. Eso sería peor que recibir un error.

## Para la semana autónoma

Una pregunta que nos quedó sobre serialización o protocolos:

¿Qué pasa si cliente y servidor usan versiones distintas del mensaje o distinto codec? En nuestro laboratorio solo recibimos un error, y nos gustaría saber cómo lo evitan JSON-RPC y gRPC.
