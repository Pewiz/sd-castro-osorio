# Observaciones — fallas provocadas · semana 4 · Equipo ______

Anoten lo que vieron, no lo que esperaban ver. Un tiempo sin unidad no sirve.

## Falla 1 — servidor muerto con el cliente conectado

Comando usado: `docker compose kill servidor`

| Pregunta | Respuesta |
|---|---|
| ¿Qué mensaje mostró el cliente? | |
| ¿Cuánto tardó en aparecer desde que enviaron el comando? (ms o s) | |
| ¿El cliente supo que el servidor estaba muerto o solo que la conexión se cerró? | |
| Al levantar el servidor de nuevo, ¿se recuperó la sesión anterior (nombre, contador)? | |

## Falla 2 — cliente sin red con el servidor vivo

Comando usado: `docker network disconnect sd_net cliente`

| Pregunta | Respuesta |
|---|---|
| ¿Qué mensaje mostró el cliente? | |
| ¿Cuánto tardó en aparecer? | |
| ¿Qué mostró el log del servidor en ese momento? | |
| Desde el punto de vista del cliente, ¿en qué se diferencia esta falla de la falla 1? | |

## Segundo cliente mientras el primero está conectado (paso 3)

| Pregunta | Respuesta |
|---|---|
| ¿El segundo cliente logró conectarse (`connect`)? | |
| ¿Recibió respuesta a su primer comando? ¿Qué mostró? | |
| ¿Qué mostró el log del servidor cuando el primer cliente hizo `SALIR`? | |

## Conclusión del equipo (3 a 5 líneas)

¿Qué falacia de la semana 2 asumiría un programador que solo probara el camino feliz de este sistema? ¿Por qué el cliente no puede distinguir entre servidor caído, servidor ocupado y red cortada?
