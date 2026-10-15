# Interfaz HTTP del servicio (anexo de protocolo.md)

> Sección 9 de `protocolo.md` v2.
> Regla de oro, la misma de la semana 6. Otro equipo debe poder usar la API leyendo SOLO este documento.

## 9.1 Identificación

| Campo | Valor |
|---|---|
| Equipo | Castro - Osorio |
| Entrada única | `http://localhost:8080` (Nginx) |
| Formato | JSON, UTF-8 |
| Documentación interactiva | `http://localhost:8080/docs` |
| Réplicas de la API | api1, api2 |
| Dónde vive el estado | en el servidor TCP, la API no guarda nada |

## 9.2 Tabla de traducción, operación por operación

| Comando del protocolo de texto | Método y ruta HTTP | Cuerpo JSON | Respuesta correcta | Código |
|---|---|---|---|---|
| `TABLA` | `GET /jugadores` | (sin cuerpo) | `{"jugadores": {"david": 0, "felipe": 0}, "replica": "api1"}` | 200 |
| `TABLA` (un jugador) | `GET /jugadores/{jugador}` | (sin cuerpo) | `{"jugador": "felipe", "puntos": 0, "replica": "api2"}` | 200 |
| `UNIR <jugador>` | `POST /jugadores` | `{"jugador": "ana"}` | `{"jugador": "ana", "puntos": 0, "replica": "api1"}` | 201 |
| `ANOTAR <jugador> <puntos>` | `POST /jugadores/{jugador}/puntos` | `{"puntos": 15}` | `{"jugador": "ana", "puntos": 15, "replica": "api2"}` | 201 |

## 9.3 Tabla de errores

| Situación | Respuesta del protocolo de texto | Código HTTP | Quién responde |
|---|---|---|---|
| El jugador no existe | `ERROR JUGADOR_NO_EXISTE` | 404 | la API |
| El jugador ya existe | `ERROR JUGADOR_YA_EXISTE` | 409 | la API |
| Cuerpo o ruta mal formados | (no llega al servidor) | 422 | la API, antes de traducir |
| El servidor TCP no está disponible | (sin respuesta) | 503 | la API |
| El servidor TCP no responde a tiempo | (sin respuesta) | 504 | la API |
| No queda ninguna réplica de la API | (sin respuesta) | 502 | Nginx |

## 9.4 Decisiones de diseño

- ¿Por qué esos sustantivos como recursos? El dato del dominio es el jugador con sus puntos, por eso `/jugadores` y `/jugadores/{jugador}/puntos`.
- ¿Qué operación NO expusieron por HTTP y por qué? `ESPERA`, porque es solo para probar concurrencia.
- ¿Qué valida la API antes de traducir, y qué pasaría si no lo validara? Que el nombre sea `^[a-z0-9_]{1,30}$` y los puntos mayores que cero. Sin eso, un nombre con espacio o salto de línea se convertiría en otro comando para el servidor.
