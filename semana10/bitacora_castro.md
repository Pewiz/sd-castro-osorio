# Bitácora individual — Semana 10

**Nombre:** Felipe Castro  **Equipo:** Castro - Osorio
**Archivo:** `semana10/bitacora_<apellido>.md` en el repositorio del equipo. **Entrega:** jueves 5 de noviembre de 2026, 18.00.

Esta bitácora es individual. Cada integrante escribe la suya con sus propias horas y sus propias palabras. No lleva nota, pero es un formativo obligatorio del programa y se revisa.

## Registro de sesiones

Una fila por sesión de trabajo. Las horas deben sumar al menos 8 entre los cuatro bloques.

| Fecha | Horas | Bloque | Qué estudié o hice | Qué me costó | Qué pregunté o respondí en el foro |
|---|---|---|---|---|---|
| | | 1 Lecturas | | | |
| | | 2 RMI, CORBA, DCOM | | | |
| | | 3 JSON-RPC 2.0 | | | |
| | | 4 Prototipo | | | |
| | | | | | |

## Tres preguntas de cierre (responder con sus palabras, 3 a 5 líneas cada una)

1. ¿Qué tienen en común JSON-RPC 2.0 y el protocolo v3 que escribieron en la semana 9? ¿Qué decisión tomó la especificación por ustedes?

Los dos mandan un mensaje con versión, id, operación, parámetros y un error. En JSON-RPC se llaman `jsonrpc`, `id`, `method`, `params` y `error`. La especificación decidió por nosotros los nombres de los campos, los códigos de error (-32601, -32602, etc.) y qué pasa con las notificaciones y los batch.

2. ¿Por qué RMI, CORBA y DCOM casi no se usan en sistemas nuevos y qué los reemplazó?

Porque cada una estaba atada a algo: RMI solo sirve para Java, DCOM sobre todo para Windows y CORBA era muy complicado. DCOM además tenía problemas con los cortafuegos. Las reemplazaron los servicios web, REST y gRPC, que usan HTTP y funcionan con cualquier lenguaje.

3. ¿Qué parte del prototipo les costó más y cómo la resolvieron?

Lo que más costó fue distinguir cuándo un error es -32602 (parámetros malos) y cuándo es -32000 (error del dominio). Lo resolvimos haciendo que `unir` y `anotar` lancen `TypeError` si los parámetros están mal y `ValueError` si el error es del dominio, por ejemplo un jugador que no existe.

## Preguntas guía del bloque 1 (2 o 3 líneas cada una)

1. ¿Qué es un stub y qué hace el stub del cliente con los parámetros antes de mandarlos?

El stub es un código que hace de intermediario: el cliente lo llama como si fuera una función normal. El stub del cliente convierte los parámetros en bytes (marshalling) y los manda por la red. Es lo mismo que hacía nuestro codec en la semana 9.

2. ¿Qué diferencia hay entre pasar un parámetro por valor y por referencia en una llamada remota, y por qué la referencia es un problema?

Por valor se manda una copia del dato. Por referencia se manda la dirección donde está el dato, pero esa dirección solo sirve en la memoria de la máquina original. En otra máquina no apunta a nada, por eso es un problema.

3. ¿Qué es un IDL y para qué sirve que el contrato esté en un archivo aparte del código?

Es un lenguaje para describir la interfaz (operaciones y tipos). Sirve porque cliente y servidor pueden generar su código desde el mismo archivo, aunque estén en lenguajes distintos. Es parecido a nuestro protocolo.md v3, pero ese solo lo leemos las personas, y el IDL (por ejemplo mensaje.proto) también lo lee una herramienta.

4. ¿Qué semántica de fallo tiene nuestro servidor de la semana 9 y por qué?

Creemos que es "al menos una vez" desde el cliente: si no llega la respuesta, el cliente puede repetir la solicitud, y una operación como `anotar` se aplicaría dos veces. El servidor no guarda qué ids ya procesó, así que no puede evitar duplicados.

5. ¿Qué agrega un objeto distribuido sobre un procedimiento remoto?

Agrega referencias remotas (el cliente guarda una referencia a un objeto del servidor) y estado, porque el objeto recuerda sus datos entre llamadas. Un procedimiento remoto solo se llama y responde.

## Ejercicios a mano del bloque 3

1. Request y response de dos operaciones del dominio, una exitosa y una con error del dominio.

```
{"jsonrpc":"2.0","method":"anotar","params":{"jugador":"felipe","puntos":15},"id":1}
{"jsonrpc":"2.0","result":{"jugador":"felipe","puntos":15},"id":1}

{"jsonrpc":"2.0","method":"anotar","params":{"jugador":"zzz","puntos":5},"id":2}
{"jsonrpc":"2.0","error":{"code":-32000,"message":"Error del dominio","data":"el jugador zzz no existe"},"id":2}
```

2. Qué responde el servidor a una request sin `jsonrpc`, a un método que no existe y a parámetros incompletos.

- Sin `jsonrpc`: error -32600 (Invalid Request).
- Método que no existe: error -32601 (Method not found).
- Parámetros incompletos: error -32602 (Invalid params).

3. Por qué una notificación no lleva `id`.

El `id` sirve para saber a qué solicitud corresponde una respuesta. Una notificación no espera respuesta, así que no lo necesita. Es la misma idea del id de la semana 9, que el cliente ponía para parear cada respuesta.

4. Las cinco decisiones en JSON-RPC sobre HTTP.

- Enmarcado: lo resuelve HTTP (el largo va en `Content-Length`), no JSON-RPC.
- Versión: el campo `jsonrpc` con el valor `"2.0"`.
- Id: el campo `id`, y la respuesta trae el mismo.
- Errores: el objeto `error` con `code`. Los de protocolo van de -32700 a -32600 y los del dominio entre -32000 y -32099.
- Tipos: los de JSON (texto, número, booleano, lista, objeto y null).

## Autoevaluación

| Afirmación | Sí | Parcial | No |
|---|---|---|---|
| Leí las secciones asignadas y puedo explicar la diferencia entre RPC y objetos distribuidos | | | |
| Aporté al cuadro comparativo con fuentes propias | | | |
| Puedo explicar el código del endpoint `/rpc` línea por línea | | | |
| Probé los seis casos de error del prototipo con `curl` | | | |
| Participé en el foro al menos una vez | | | |
