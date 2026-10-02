# Protocolo de aplicación — versión 2

> Plantilla de la Semana 6. Reemplazar cada sección con el protocolo del equipo.
> Regla de oro — otro equipo debe poder escribir un cliente compatible leyendo SOLO este documento.

## 1. Identificación

| Campo | Valor |
|---|---|
| Equipo | (nombre del equipo) |
| Dominio del servicio | (inventario, saldos, sala de partida, sensores, mensajería…) |
| Versión del protocolo | 2.0 |
| Transporte | TCP, puerto 5000 |
| Codificación | UTF-8, un mensaje por línea, terminador `\n` |
| Modelo de concurrencia del servidor | hilo por cliente |
| Timeout de inactividad | 60 s (el servidor cierra la conexión) |

## 2. Formato general

- Petición `COMANDO [argumentos separados por espacio]\n`
- Respuesta correcta `OK [datos]\n`
- Respuesta de error `ERROR CODIGO [detalle]\n`
- El servidor responde exactamente UNA línea por cada línea recibida.
- Los comandos no distinguen mayúsculas; los argumentos sí.

## 3. Secuencia de una sesión

```
cliente                          servidor
   |--- HOLA <nombre> ------------->|
   |<-- OK HOLA <nombre> -----------|
   |--- <operaciones...> ---------->|
   |<-- OK ... / ERROR ... ---------|
   |--- SALIR --------------------->|
   |<-- OK CHAO --------------------|   (el servidor cierra)
```

¿Es obligatorio HOLA antes de operar? (indicar sí o no y qué pasa si no se envía)

## 4. Operaciones

| Comando | Argumentos | Respuesta OK | Errores posibles | ¿Modifica estado compartido? |
|---|---|---|---|---|
| HOLA | nombre | `OK HOLA nombre` | — | no |
| LISTAR | — | `OK item:cant item:cant …` | — | no |
| AGREGAR | item cantidad | `OK item nuevo_total` | `ERROR FORMATO …` | sí |
| QUITAR | item cantidad | `OK item nuevo_total` | `ERROR FORMATO …`, `ERROR ITEM_NO_EXISTE`, `ERROR STOCK_INSUFICIENTE actual` | sí |
| ESPERA | segundos | `OK ESPERA seg` | `ERROR FORMATO …` | no |
| SALIR | — | `OK CHAO` | — | no |

(Mínimo tres operaciones propias del dominio, al menos una que modifique estado compartido.)

## 5. Códigos de error

| Código | Cuándo se produce |
|---|---|
| COMANDO_DESCONOCIDO | el comando no está en la tabla |
| FORMATO | faltan o sobran argumentos, o el tipo es incorrecto |
| ITEM_NO_EXISTE | (ejemplo del dominio) |
| STOCK_INSUFICIENTE | (ejemplo del dominio) |

## 6. Comportamiento ante situaciones anómalas

| Situación | Qué hace el servidor |
|---|---|
| Línea vacía | responde `ERROR COMANDO_DESCONOCIDO` |
| Cliente inactivo 60 s | cierra la conexión sin mensaje |
| Cliente se desconecta a mitad de una operación | registra la desconexión y sigue atendiendo a los demás |
| Dos clientes modifican el mismo dato a la vez | las operaciones se serializan con un Lock; el resultado es el mismo que si hubieran llegado una tras otra |
| Bytes no decodificables en UTF-8 | (indicar) |

## 7. Estado compartido

| Dato | Tipo | Valor inicial | Quién lo modifica |
|---|---|---|---|
| inventario | dict item → cantidad | manzana 100, pera 100 | AGREGAR, QUITAR |
| operaciones | int | 0 | toda operación del dominio |

## 8. Historial de cambios

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | semana 4 | protocolo inicial, servidor secuencial |
| 2.0 | semana 6 | servidor concurrente, estado compartido, errores y timeout documentados |
