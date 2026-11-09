# Bitácora individual — Semana 10

**Nombre:** David Osorio  **Equipo:** Castro - Osorio
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

Se parecen en que los dos tienen versión, id para parear la respuesta y una forma de avisar errores. La diferencia es que JSON-RPC ya trae todo definido (nombres, códigos y formato del error) y en la semana 9 lo definimos nosotros en protocolo.md.

2. ¿Por qué RMI, CORBA y DCOM casi no se usan en sistemas nuevos y qué los reemplazó?

Porque cada una dependía de algo: RMI de Java, DCOM de Windows y CORBA era difícil de usar. Hoy se usan REST, gRPC o JSON-RPC, que van sobre HTTP y los entiende cualquier lenguaje.

3. ¿Qué parte del prototipo les costó más y cómo la resolvieron?

Lo más difícil fue entender las notificaciones: se ejecutan pero el servidor no responde nada (HTTP 204). Lo probamos con `curl` agregando al jugador `pedro` sin id y vimos que no devolvía cuerpo, pero el jugador sí se agregaba.

## Preguntas guía del bloque 1 (2 o 3 líneas cada una)

1. ¿Qué es un stub y qué hace el stub del cliente con los parámetros antes de mandarlos?

Es el código que representa al servidor en el lado del cliente. Recibe la llamada, empaqueta los parámetros en bytes (marshalling) y los envía. En la semana 9 eso lo hacía `codec.py`.

2. ¿Qué diferencia hay entre pasar un parámetro por valor y por referencia en una llamada remota, y por qué la referencia es un problema?

Por valor viaja una copia del dato. Por referencia viaja una dirección de memoria, y esa dirección no vale en otra máquina porque ahí la memoria es distinta.

3. ¿Qué es un IDL y para qué sirve que el contrato esté en un archivo aparte del código?

Es un archivo que describe las operaciones y los tipos. Con él, cliente y servidor generan su código y se aseguran de hablar igual, incluso en lenguajes distintos. Nuestro protocolo.md cumple algo parecido, pero lo leen personas y no una herramienta.

4. ¿Qué semántica de fallo tiene nuestro servidor de la semana 9 y por qué?

"Al menos una vez" si el cliente reintenta: si la respuesta se pierde y el cliente repite `ANOTAR`, el servidor suma los puntos otra vez, porque no recuerda las solicitudes anteriores.

5. ¿Qué agrega un objeto distribuido sobre un procedimiento remoto?

Que el cliente puede tener una referencia a un objeto que vive en el servidor, y ese objeto guarda su estado entre llamadas.

## Ejercicios a mano del bloque 3

1. Request y response de dos operaciones del dominio, una exitosa y una con error del dominio.

```
{"jsonrpc":"2.0","method":"unir","params":{"jugador":"ana"},"id":1}
{"jsonrpc":"2.0","result":{"jugador":"ana","puntos":0},"id":1}

{"jsonrpc":"2.0","method":"unir","params":{"jugador":"ana"},"id":2}
{"jsonrpc":"2.0","error":{"code":-32000,"message":"Error del dominio","data":"el jugador ana ya existe"},"id":2}
```

2. Qué responde el servidor a una request sin `jsonrpc`, a un método que no existe y a parámetros incompletos.

- Sin `jsonrpc`: -32600 (Invalid Request).
- Método que no existe: -32601 (Method not found).
- Parámetros incompletos: -32602 (Invalid params).

3. Por qué una notificación no lleva `id`.

Porque el `id` es para saber a qué solicitud responde una respuesta, y una notificación no recibe respuesta. Es como el id de la semana 9, que el cliente usaba para parear.

4. Las cinco decisiones en JSON-RPC sobre HTTP.

- Enmarcado: lo hace HTTP, no JSON-RPC.
- Versión: campo `jsonrpc` con `"2.0"`.
- Id: campo `id`, que se repite en la respuesta.
- Errores: objeto `error` con `code`. Los del protocolo tienen códigos fijos (-32700 a -32600) y los del dominio van entre -32000 y -32099.
- Tipos: los de JSON (texto, número, booleano, lista, objeto y null).

## Autoevaluación

| Afirmación | Sí | Parcial | No |
|---|---|---|---|
| Leí las secciones asignadas y puedo explicar la diferencia entre RPC y objetos distribuidos | | | |
| Aporté al cuadro comparativo con fuentes propias | | | |
| Puedo explicar el código del endpoint `/rpc` línea por línea | | | |
| Probé los seis casos de error del prototipo con `curl` | | | |
| Participé en el foro al menos una vez | | | |
