# Semana 11 · RPC y migración a gRPC

| Carpeta | Para qué |
|---|---|
| `demo/` | Demo del jueves 5-11. Semánticas de fallo maybe, at-least-once y at-most-once sobre JSON-RPC |
| `laboratorio/` | Plantilla del viernes 6-11. Se copia como `semana11/` en el repositorio del equipo |

## Laboratorio en cinco comandos

```bash
cp -r laboratorio ../mi-repo/semana11
cd ../mi-repo/semana11
docker compose build                                     # instala grpcio y grpcio-tools (necesita red)
docker compose run --rm --no-deps servidor sh generar.sh # genera servicio_pb2.py y servicio_pb2_grpc.py
docker compose up -d
docker compose exec cliente python cliente_grpc.py agregar tornillo 25
```

| Archivo | Qué es |
|---|---|
| `proto/servicio.proto` | El contrato, IDL de Protocol Buffers. Se reemplaza por el del dominio del equipo |
| `dominio.py` | Las funciones del dominio, sin red. Las mismas de `semana10/rpc.py` |
| `rpc.py` | JSON-RPC de la semana 10, ahora importando `dominio.py` |
| `servidor_grpc.py` | Servidor gRPC con `FALLA`, `DEMORA` y `DEDUP` |
| `cliente_grpc.py` | Cliente con deadline, reintentos e `id_solicitud` |
| `generar.sh` | Genera los stubs desde el `.proto` |
| `observaciones.md` | Registro del laboratorio, se entrega hoy antes de las 16.00 |
| `contrato.md` | Trabajo autónomo, plazo jueves 12-11 a las 18.00 |

Si no hay Docker, todo corre con Python local. `pip install -r requirements.txt`, generar los stubs con `python -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. proto/servicio.proto`, `export SERVIDOR_HOST=127.0.0.1` (en PowerShell `$env:SERVIDOR_HOST="127.0.0.1"`) y dos terminales.

En PowerShell las variables se definen antes del comando, por ejemplo `$env:FALLA="siempre"; docker compose up -d servidor`, y quedan puestas hasta `Remove-Item Env:FALLA`.
