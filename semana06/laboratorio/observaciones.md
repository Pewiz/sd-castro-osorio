# Observaciones — Semana 6

Equipo:
Integrantes:
Dominio del servicio:

## Paso 1 — servidor secuencial bajo carga

Comando ejecutado:
Tiempo por cliente:
TOTAL:
¿Qué esperaban? ¿Qué observaron?

## Paso 2 — hilo por cliente bajo carga

Comando ejecutado:
TOTAL:
Diferencia respecto al Paso 1 y explicación:

## Paso 3 — condición de carrera

Operación que modifica estado compartido usada:
Valor esperado:
Valor observado SIN Lock:
Valor observado CON Lock:
¿Dónde exactamente está la sección crítica en su código?

## Paso 4 — despliegue con docker compose

Salida de `docker compose ps`:
IP del host publicada para la prueba cruzada:

## Paso 5 — prueba cruzada

Equipo cuyo servidor probamos:
¿Su protocolo.md alcanzó para conectarse sin preguntar? (sí / no, qué faltó)
Mensajes enviados y respuestas obtenidas:
Qué falló y por qué:

Equipo que probó nuestro servidor:
Qué reportaron:

## Falla provocada — desconexión abrupta

Comando usado para provocarla:
Qué registró el log del servidor:
¿El servidor siguió atendiendo a los demás? Evidencia:
