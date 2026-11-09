# Semana 10 — Trabajo autónomo (26 al 30 de octubre de 2026)

Sin sesiones por la Semana de Vida Universitaria. Ocho horas de trabajo guiado por la guía `Semana_10_Guia_Autonoma.docx`.

| Archivo | Para qué |
|---|---|
| `rpc.py` | Esqueleto del prototipo JSON-RPC 2.0 sobre FastAPI. Se completa con dos operaciones del dominio del equipo |
| `cuadro_comparativo.md` | Plantilla del cuadro RMI / CORBA / DCOM / JSON-RPC. Uno por equipo |
| `bitacora_plantilla.md` | Formato de la bitácora individual. Uno por integrante, `bitacora_<apellido>.md` |

Todo se entrega en `semana10/` del repositorio del equipo antes del jueves 5 de noviembre a las 18.00.

```bash
# correr el prototipo dentro del contenedor api de semana07 o con Python local
pip install fastapi uvicorn
uvicorn rpc:app --host 0.0.0.0 --port 8000
curl -s -X POST localhost:8000/rpc -H 'Content-Type: application/json' \
     -d '{"jsonrpc":"2.0","method":"listar","id":1}'
```
