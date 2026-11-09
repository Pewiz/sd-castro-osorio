# Contrato del servicio · trabajo autónomo semana 11

Plazo jueves 12-11-2026 a las 18.00, en `semana11/` del repositorio del equipo.

## Qué hay que hacer
1. Agregar al menos **una operación nueva** a `proto/servicio.proto` con sus mensajes, sin cambiar los números de campo existentes.
2. Implementarla en `dominio.py` y exponerla en `servidor_grpc.py` y en `cliente_grpc.py`.
3. Regenerar los stubs y probarla desde el contenedor cliente.
4. Completar este archivo.

## Operaciones

| Operación | Qué hace | Modifica estado | Idempotente | Lleva `id_solicitud` | Errores posibles (código gRPC) |
|---|---|---|---|---|---|
| | | | | | |

## Mensajes y campos

| Mensaje | Campo | Número | Tipo | Significado |
|---|---|---|---|---|
| | | | | |

## Decisiones
- ¿Por qué la operación nueva es o no es idempotente?
- ¿Qué pasaría si un cliente antiguo, que no conoce la operación nueva, sigue llamando al servidor? (pista, compatibilidad de Protocol Buffers)
- Prueba realizada (comando y salida)
