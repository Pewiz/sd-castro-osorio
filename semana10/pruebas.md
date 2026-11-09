# Pruebas del prototipo JSON-RPC

Servidor: `uvicorn rpc:app --host 0.0.0.0 --port 8000`. Operaciones del dominio: `unir` y `anotar`.
Las respuestas son las que devolvió el servidor al correr cada comando.

## Caso 1 — unir, params como objeto

Esperado: result

```
$ curl -s -X POST localhost:8000/rpc -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","method":"unir","params":{"jugador":"ana"},"id":1}'
{"jsonrpc":"2.0","result":{"jugador":"ana","puntos":0},"id":1}
```

## Caso 2 — anotar, params como lista

Esperado: result

```
$ curl -s -X POST localhost:8000/rpc -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","method":"anotar","params":["ana",15],"id":2}'
{"jsonrpc":"2.0","result":{"jugador":"ana","puntos":15},"id":2}
```

## Caso 3 — error del dominio (jugador que no existe)

Esperado: -32000 con data

```
$ curl -s -X POST localhost:8000/rpc -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","method":"anotar","params":{"jugador":"zzz","puntos":5},"id":3}'
{"jsonrpc":"2.0","error":{"code":-32000,"message":"Error del dominio","data":"el jugador zzz no existe"},"id":3}
```

## Caso 4 — método inexistente

Esperado: -32601

```
$ curl -s -X POST localhost:8000/rpc -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","method":"quitar","id":4}'
{"jsonrpc":"2.0","error":{"code":-32601,"message":"Method not found"},"id":4}
```

## Caso 5 — parámetros incompletos

Esperado: -32602

```
$ curl -s -X POST localhost:8000/rpc -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","method":"anotar","params":{"jugador":"ana"},"id":5}'
{"jsonrpc":"2.0","error":{"code":-32602,"message":"Invalid params","data":"anotar() missing 1 required positional argument: 'puntos'"},"id":5}
```

## Caso 5b — parámetro de tipo incorrecto (puntos con texto)

Esperado: -32602

```
$ curl -s -X POST localhost:8000/rpc -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","method":"anotar","params":["ana","abc"],"id":6}'
{"jsonrpc":"2.0","error":{"code":-32602,"message":"Invalid params","data":"jugador debe ser texto y puntos un entero"},"id":6}
```

## Caso 6 — JSON inválido

Esperado: -32700

```
$ curl -s -X POST localhost:8000/rpc -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0", "method": '
{"jsonrpc":"2.0","error":{"code":-32700,"message":"Parse error"},"id":null}
```

## Caso 7 — request sin jsonrpc

Esperado: -32600

```
$ curl -s -X POST localhost:8000/rpc -H 'Content-Type: application/json' -d '{"method":"unir","params":{"jugador":"luis"},"id":7}'
{"jsonrpc":"2.0","error":{"code":-32600,"message":"Invalid Request"},"id":7}
```

## Caso 8 — notificación (sin id)

Esperado: sin cuerpo, HTTP 204

```
$ curl -s -i -X POST localhost:8000/rpc -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","method":"unir","params":{"jugador":"pedro"}}' | head -1
HTTP/1.1 204 No Content
```

## Caso 9 — batch con una válida y una inexistente

Esperado: lista con un result y un -32601

```
$ curl -s -X POST localhost:8000/rpc -H 'Content-Type: application/json' -d '[{"jsonrpc":"2.0","method":"anotar","params":{"jugador":"felipe","puntos":3},"id":"a"},{"jsonrpc":"2.0","method":"quitar","id":"b"}]'
[{"jsonrpc":"2.0","result":{"jugador":"felipe","puntos":3},"id":"a"},{"jsonrpc":"2.0","error":{"code":-32601,"message":"Method not found"},"id":"b"}]
```

## Notas

- En el caso 8 el jugador `pedro` sí se agrega, porque una notificación se ejecuta pero no responde.
- Los jugadores viven en la memoria del proceso: si se reinicia el servidor, vuelven a `david` y `felipe`.
