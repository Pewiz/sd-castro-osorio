# Observaciones — fallas provocadas · semana 4 · Equipo Castro - Osorio

Anoten lo que vieron, no lo que esperaban ver. Un tiempo sin unidad no sirve.

## Falla 1 — servidor muerto con el cliente conectado

Comando usado: `docker compose kill servidor`

El cliente ya estaba adentro (`HOLA equipo`, `CONTAR` → `OK 2`). Ahí matamos el servidor y mandamos `ECO`.

| Pregunta | Respuesta |
|---|---|
| ¿Qué mensaje mostró el cliente? | `CONEXIÓN PERDIDA: ConnectionError: el servidor cerró la conexión sin responder` |
| ¿Cuánto tardó en aparecer desde que enviaron el comando? (ms o s) | Menos de 1 ms. Apareció al tiro. |
| ¿El cliente supo que el servidor estaba muerto o solo que la conexión se cerró? | Solo que se cerró. El texto dice que cerraron sin responder, no que el servidor murió. |
| Al levantar el servidor de nuevo, ¿se recuperó la sesión anterior (nombre, contador)? | No. Antes el contador iba en 2. Al volver a levantarlo, un `CONTAR` nuevo dio `OK 1`. El nombre tampoco quedó. |

## Falla 2 — cliente sin red con el servidor vivo

Comando usado: `docker network disconnect sd_net cliente`

Misma sesión: `HOLA` y `CONTAR` andaban. Cortamos la red del cliente y mandamos `ECO`.

| Pregunta | Respuesta |
|---|---|
| ¿Qué mensaje mostró el cliente? | `TIMEOUT: el servidor no respondió en 5 s. ¿Caído, sin red o lento? No se puede saber.` |
| ¿Cuánto tardó en aparecer? | 5.0 s |
| ¿Qué mostró el log del servidor en ese momento? | Nada. Se quedó en el `CONTAR` de antes. No anotó cierre ni desconexión. |
| Desde el punto de vista del cliente, ¿en qué se diferencia esta falla de la falla 1? | En la falla 1 se cortó al instante. Acá se quedó callado 5 segundos y después dijo que no sabe qué pasó. Se sienten distintas. |

## Segundo cliente mientras el primero está conectado (paso 3)

El primero hizo `HOLA primero` y se quedó. El segundo mandó `HOLA segundo` sin esperar.

| Pregunta | Respuesta |
|---|---|
| ¿El segundo cliente logró conectarse (`connect`)? | Sí, al tiro. Dijo `conectado desde 172.20.0.3:53368` aunque el primero seguía adentro. |
| ¿Recibió respuesta a su primer comando? ¿Qué mostró? | No la vio. A los 5.0 s salió el mismo `TIMEOUT` de la falla 2. El servidor sí tenía el `OK hola segundo`, pero lo mandó recién cuando el primero salió, y para entonces el segundo ya se había ido. |
| ¿Qué mostró el log del servidor cuando el primer cliente hizo `SALIR`? | `SALIR` → `ADIOS`, cierre del primero (2 mensajes), y ahí recién apareció el segundo: `HOLA segundo` → `OK hola segundo`, y cierre (1 mensaje). |

## Conclusión del equipo (3 a 5 líneas)

Si solo probáramos que `HOLA` responde `OK`, diríamos que esto siempre funciona. Es la falacia de la semana 2: la red es confiable y la respuesta llega al tiro. No es así. Servidor ocupado y red cortada muestran el mismo mensaje, el `TIMEOUT` de 5 s, que incluso dice que no se puede saber si se cayó, si no hay red o si está lento. El servidor muerto sí avisó al instante, pero igual solo dijo que la conexión se cerró, no por qué.
