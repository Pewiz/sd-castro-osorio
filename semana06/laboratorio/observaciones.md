# Observaciones — Semana 6

Equipo: Castro - Osorio
Integrantes: David Osorio / Felipe Castro
Dominio del servicio: Juegos (tabla de puntajes: TABLA, UNIR, ANOTAR)

## Paso 1 — servidor secuencial bajo carga

Comando ejecutado (demo, `servidor_secuencial.py`; el de `laboratorio/` ya es hilo por cliente):

```bash
cd semana06/demo
docker compose up -d --build
docker compose exec carga python cliente_carga.py --clientes 5 --comando "ESPERA 2"
```

Tiempo por cliente: cada `ESPERA 2` tardó 2.00 s de operación. El tiempo en fila fue 0.01, 2.01, 4.01, 6.01 y 8.01 s (totales individuales 2.01, 4.01, 6.01, 8.01 y 10.01 s).
TOTAL: 10.02 s
¿Qué esperaban? ¿Qué observaron? Esperábamos unos 10 segundos, porque son 5 clientes de 2 segundos y el servidor atiende de a uno. Salió justo eso: 10.02 s. Se nota en la fila: el primero entra al tiro y el último espera como 8 segundos.

## Paso 2 — hilo por cliente bajo carga

Comando ejecutado:

```bash
cd semana06/laboratorio
docker compose up -d --build
docker compose exec carga python cliente_carga.py --clientes 5 --comando "ESPERA 2"
```

TOTAL: 2.02 s
Diferencia respecto al Paso 1 y explicación: acá se demoró lo mismo que un solo cliente, 2.02 s. Los cinco entraron juntos y ninguno esperó en fila. En el paso 1 los tiempos se sumaban; acá se hacen al mismo tiempo, porque la espera no se bloquea entre clientes.

## Paso 3 — condición de carrera

Operación que modifica estado compartido usada: `ANOTAR felipe 1`, 20 clientes × 50 repeticiones.

```bash
docker compose exec carga python cliente_carga.py --clientes 20 --comando "ANOTAR felipe 1" --repeticiones 50
```

Sin Lock: `SIN_LOCK=1 docker compose up -d --force-recreate servidor` y el mismo comando. Lectura final con `TABLA`.

Valor esperado: 1000 (felipe partía en 0)
Valor observado SIN Lock: `felipe:106` (TOTAL de la carga: 0.18 s)
Valor observado CON Lock: `felipe:1000` (TOTAL de la carga: 1.16 s)
¿Dónde exactamente está la sección crítica en su código? En `op_anotar` (`servidor.py`), dentro del `with seccion_critica()`: lee el puntaje de felipe, espera 1 ms y lo guarda sumado. Sin el Lock se pierden puntos, porque dos clientes leen el mismo número y el que escribe después le pisa el cambio al otro. Con el Lock dio los 1000 justos.

## Paso 4 — despliegue con docker compose

Salida de `docker compose ps`:

```
NAME          IMAGE                  COMMAND                SERVICE    STATUS          PORTS
sd_carga      laboratorio-carga      "sleep infinity"       carga      Up
sd_cliente    laboratorio-cliente    "sleep infinity"       cliente    Up
sd_servidor   laboratorio-servidor   "python servidor.py"   servidor   Up              0.0.0.0:5000->5000/tcp
```

IP del host publicada para la prueba cruzada: 192.168.1.110:5000

## Paso 5 — prueba cruzada

Equipo cuyo servidor probamos:
¿Su protocolo.md alcanzó para conectarse sin preguntar? (sí / no, qué faltó)
Mensajes enviados y respuestas obtenidas:
Qué falló y por qué:

Equipo que probó nuestro servidor:
Qué reportaron:

## Falla provocada — desconexión abrupta

Comando usado para provocarla:

```bash
docker compose exec -d carga python cliente_carga.py --clientes 3 --comando "ESPERA 5"
# ~1 s después:
docker compose kill carga
"HOLA prueba" | docker compose exec -T cliente python cliente.py
```

Qué registró el log del servidor: se conectaron los tres clientes de carga (`172.20.0.3`) y unos 5 segundos después el servidor anotó el cierre de cada uno. No apareció el aviso de desconexión abrupta; simplemente los cerró cuando terminó la espera.
¿El servidor siguió atendiendo a los demás? Evidencia: sí. Mientras esos tres seguían en la espera, otro cliente pudo entrar y recibió `OK HOLA prueba`, `OK david:0 felipe:0` y `OK CHAO`. El corte de unos no botó al resto.
