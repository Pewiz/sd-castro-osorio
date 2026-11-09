# Protocolo del servicio — versión 3 (Semana 9)

## 1. Identificación

| Campo | Valor |
|---|---|
| Equipo | Castro - Osorio |
| Dominio | Juegos, tabla de puntajes |
| Versión del protocolo | 2 (campo `version` del mensaje) |
| Versión del documento | 3 |
| Transporte | TCP, puerto 5000 dentro de `sd_net` |

## 2. Formato del mensaje

Cada mensaje viaja **enmarcado**: 4 bytes con el largo (entero sin signo, big-endian) seguidos del cuerpo.

```
+------------+------------------------+
| largo (4B) | cuerpo (largo bytes)   |
+------------+------------------------+
```

El cuerpo se codifica con uno de dos **codecs**, elegido por la variable `CODEC`. Cliente y servidor deben usar el mismo.

### 2.1 Solicitud (cliente → servidor)

| Campo | Tipo | Descripción |
|---|---|---|
| `version` | entero | Versión del protocolo. El servidor rechaza las distintas de 2 |
| `id` | entero | Correlativo del cliente. La respuesta trae el mismo id |
| `operacion` | texto | Nombre de la operación en mayúsculas |
| `argumentos` | lista de textos | Argumentos de la operación, puede ser vacía |

### 2.2 Respuesta (servidor → cliente)

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | entero | Mismo id de la solicitud (0 si no se pudo leer la solicitud) |
| `estado` | `OK` o `ERROR` | Resultado |
| `datos` | lista de textos | Resultado cuando estado es OK |
| `error` | texto | Mensaje legible cuando estado es ERROR |

### 2.3 Codec `json`

Cuerpo en JSON UTF-8 con los campos anteriores como claves.

```json
{"operacion": "ANOTAR", "argumentos": ["felipe", "15"], "id": 7, "version": 2}
```

### 2.4 Codec `bin`

Cuerpo binario con `struct`, big-endian. Los textos van con largo prefijado de 2 bytes y las listas con cantidad prefijada de 1 byte.

```
Solicitud: version(1B) id(4B) operacion(2B+texto) n_args(1B) [arg(2B+texto)]*
Respuesta: id(4B) estado(1B: 0=OK 1=ERROR) n_datos(1B) [dato(2B+texto)]* error(2B+texto)
```

## 3. Operaciones

| Operación | Argumentos | Respuesta OK (`datos`) | Errores posibles |
|---|---|---|---|
| `HOLA` | nombre (opcional) | `HOLA <nombre>` (o `anonimo`) | — |
| `TABLA` | — | un `jugador:puntos` por jugador, ordenado por nombre | — |
| `UNIR` | jugador | `[jugador, "0"]` | `FORMATO UNIR <jugador>`, `JUGADOR_YA_EXISTE` |
| `ANOTAR` | jugador, puntos | `[jugador, puntos_nuevos]` | `FORMATO ANOTAR <jugador> <puntos>`, `JUGADOR_NO_EXISTE` |
| `ESPERA` | segundos | `ESPERA <segundos>` | `FORMATO ESPERA <segundos>` |
| `SALIR` | — | `CHAO`, cierra la conexión | — |

Los errores de dominio van en el campo `error` como `CODIGO detalle`; la API HTTP traduce ese código a un estado HTTP.
## 4. Errores de protocolo

| Situación | Reacción del servidor |
|---|---|
| `version` distinta de 2 | Responde `ERROR` con el texto `versión X no soportada, use 2` y mantiene la conexión |
| Cuerpo que no se puede decodificar | Responde `ERROR mensaje mal formado (...)` con id 0 y **cierra esa conexión** |
| Largo anunciado mayor a 1 MB | Responde `ERROR` y cierra esa conexión |
| Largo anunciado mayor a lo enviado | Espera hasta `TIMEOUT_SERVIDOR` (30 s) y cierra esa conexión |
| Operación desconocida | Responde `ERROR COMANDO_DESCONOCIDO <op>` y mantiene la conexión |

## 5. Concurrencia

Un hilo por conexión y un `Lock` sobre el estado compartido (`puntajes`). `ESPERA` no toma el `Lock`.

## 6. Ejemplo de sesión

```
> HOLA felipe               ->  OK HOLA felipe
> UNIR ana                  ->  OK ana | 0
> ANOTAR ana 15             ->  OK ana | 15
> ANOTAR zzz 5              ->  ERROR JUGADOR_NO_EXISTE
> TABLA                     ->  OK ana:15 | david:0 | felipe:0
> SALIR                     ->  OK CHAO
```

## 7. Medición de codecs

Salida de `python bench_codec.py 10000` (10 000 solicitudes y 10 000 respuestas del dominio JUEGOS, dentro del contenedor):

| Mensaje   | Codec | Bytes promedio | Bytes totales | Codificar (ms) | Decodificar (ms) |
|-----------|-------|---------------:|--------------:|---------------:|-----------------:|
| Solicitud | json  |           73.3 |        733186 |           41.7 |             20.5 |
| Solicitud | bin   |           19.8 |        197534 |            8.6 |             11.4 |
| Respuesta | json  |          102.4 |       1024304 |           44.1 |             21.2 |
| Respuesta | bin   |           50.5 |        505414 |           13.1 |             16.2 |

El binario ocupa 73 % menos en la solicitud y 51 % menos en la respuesta, y es más rápido en codificar y decodificar. Lo malo es que no se puede leer a simple vista y los dos lados tienen que usar el mismo codec.

La respuesta ahorra menos porque casi todo lo que lleva son textos (nombres y puntajes), que ocupan lo mismo en los dos formatos. El binario solo se ahorra llaves, comillas y nombres de campo, y eso pesa más en la solicitud, que es más corta.

## 8. Historial de cambios

| Versión doc | Fecha | Cambio |
|---|---|---|
| 3 | sem. 9 | Mensaje estructurado, enmarcado por largo, codecs json y bin, versión en el mensaje |
