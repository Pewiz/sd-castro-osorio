# Demo del jueves · semánticas de fallo con JSON-RPC

Material del docente. Servidor JSON-RPC con el dominio de inventario de la semana 10 y dos perillas, `FALLA` y `DEDUP`.

```bash
docker compose up -d --build
alias c='docker compose exec cliente'

# 0 · normal
c python cliente_reintento.py agregar tornillo 25

# 1 · maybe, el cliente no reintenta y no sabe qué pasó
FALLA=primera docker compose up -d servidor
c python cliente_reintento.py agregar tornillo 25
c python cliente_reintento.py listar          # tornillo 25, se aplicó igual

# 2 · at-least-once, reintenta y duplica
docker compose restart servidor               # borra el estado y rearma la falla
c python cliente_reintento.py agregar tornillo 25 --reintentos 1
c python cliente_reintento.py listar          # tornillo 50

# 3 · at-most-once, el servidor reconoce el reintento por el id
FALLA=primera DEDUP=1 docker compose up -d servidor
c python cliente_reintento.py agregar tornillo 25 --reintentos 1
c python cliente_reintento.py listar          # tornillo 25

docker compose logs servidor
docker compose down -v
```
