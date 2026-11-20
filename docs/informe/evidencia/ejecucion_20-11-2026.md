# Evidencia de ejecución · 20-11-2026

Salidas copiadas tal cual de la terminal. Sirven de respaldo a la sección 5 del informe.

## 1. gRPC entre contenedores (semana11/laboratorio)

```text
$ docker compose up -d --build
$ docker compose ps
NAME          IMAGE              COMMAND                  SERVICE    STATUS        PORTS
sd_cliente    sd_grpc:semana11   "sleep infinity"         cliente    Up            
sd_servidor   sd_grpc:semana11   "python servidor_grp…"   servidor   Up 1 second   0.0.0.0:50051->50051/tcp, [::]:50051->50051/tcp

$ docker compose exec cliente python cliente_grpc.py tabla
[cliente] intento 1, id_solicitud=-, deadline 2 s
[cliente]   david=0, felipe=0
$ docker compose exec cliente python cliente_grpc.py unir ana
[cliente] intento 1, id_solicitud=c255ebcc, deadline 2 s
[cliente]   OK ana puntos=0
$ docker compose exec cliente python cliente_grpc.py anotar ana 15
[cliente] intento 1, id_solicitud=06ef2967, deadline 2 s
[cliente]   OK ana puntos=15
$ docker compose exec cliente python cliente_grpc.py tabla
[cliente] intento 1, id_solicitud=-, deadline 2 s
[cliente]   ana=15, david=0, felipe=0

$ docker compose exec cliente hostname -i
172.19.0.3
$ docker compose exec servidor hostname -i
172.19.0.2
```

## 2. JSON-RPC sobre el mismo dominio (semana11/laboratorio, solo para la medición)

`rpc.py` ya estaba en la carpeta y usa el mismo `dominio.py`. Se levantó como un segundo proceso dentro de `sd_servidor`,
sin cambiar código ni compose. Antes se reinició el servidor para que la tabla volviera al estado inicial.

```text
$ docker compose restart servidor
$ docker compose exec -d servidor uvicorn rpc:app --host 0.0.0.0 --port 8000
$ docker compose exec cliente python -c "...POST http://servidor:8000/rpc {'jsonrpc':'2.0','method':'tabla','id':1}..."
{"jsonrpc":"2.0","result":{"david":0,"felipe":0},"id":1}
```

## 3. Pyro5 entre contenedores (semana12/laboratorio)

```text
$ docker compose up -d --build
$ docker compose ps
NAME          IMAGE                  COMMAND                  SERVICE    STATUS
sd_cliente    laboratorio-cliente    "sleep infinity"         cliente    Up 4 seconds
sd_nombres    laboratorio-nombres    "python -m Pyro5.nam…"   nombres    Up 5 seconds
sd_servidor   laboratorio-servidor   "python servidor_pyr…"   servidor   Up 5 seconds

$ docker compose logs servidor
sd_servidor  | 15:40:41 [servidor] daemon escuchando, modo de instancia single
sd_servidor  | 15:40:41 [servidor] URI PYRO:juegos@servidor:9100
sd_servidor  | 15:40:41 [servidor] registrado como sd.castro-osorio.juegos

$ docker compose exec cliente python cliente_pyro.py uri
15:40:47 sd.castro-osorio.juegos -> PYRO:juegos@servidor:9100
15:40:47 nombres registrados ['Pyro.NameServer', 'sd.castro-osorio.juegos']
$ docker compose exec cliente python cliente_pyro.py tabla
15:40:47 tabla {'david': 0, 'felipe': 0}
$ docker compose exec cliente python cliente_pyro.py partida david 5
15:40:48 recibí Proxy, referencia PYRO:obj_0f61f4e96ba544b5b0f8dbb13ae8992d@servidor:9100
15:40:48 estado en el servidor {'jugador': 'david', 'puntos': 5}
15:40:48 finalizar -> {'jugador': 'david', 'puntos': 5}
15:40:48 uso la referencia después de finalizar
15:40:48 ERROR del daemon. La referencia apunta a un objeto que ya no existe. unknown object
$ docker compose exec cliente python cliente_pyro.py vivas
15:40:49 partidas vivas en el servidor 0

$ docker compose exec cliente hostname -i     -> 172.19.0.4
$ docker compose exec servidor hostname -i    -> 172.19.0.3
$ docker compose exec nombres hostname -i     -> 172.19.0.2
```

## 4. Medición con medir.py (n = 200, operación de consulta `tabla`, tabla inicial david=0, felipe=0)

Comandos

```text
# semana11/laboratorio (medir.py con las tres líneas EDITAR apuntando a PartidaStub y Tabla)
docker compose exec cliente python medir.py grpc --metodo tabla
docker compose exec cliente python medir.py jsonrpc --url http://servidor:8000/rpc --metodo tabla

# semana12/laboratorio (el objeto se llama sd.castro-osorio.juegos)
docker compose restart servidor
docker compose exec cliente python medir.py pyro --nombre sd.castro-osorio.juegos --metodo tabla
docker compose cp cliente:/app/mediciones.csv ./mediciones.csv
```

Salida (tres corridas por mecanismo, en el orden en que se ejecutaron)

```text
| Mecanismo | Operación | n | p50 ms | p95 ms | media ms | máx ms | respuesta bytes |
|---|---|---|---|---|---|---|---|
| grpc    | tabla | 200 | 1.18 | 1.89 | 1.28 | 3.1  | 19 |
| jsonrpc | tabla | 200 | 1.88 | 2.89 | 1.98 | 4.77 | 56 |
| grpc    | tabla | 200 | 1.0  | 1.24 | 1.02 | 1.5  | 19 |
| jsonrpc | tabla | 200 | 1.56 | 2.0  | 1.6  | 3.46 | 56 |
| grpc    | tabla | 200 | 1.03 | 1.24 | 1.06 | 3.37 | 19 |
| jsonrpc | tabla | 200 | 1.89 | 2.83 | 1.98 | 3.16 | 56 |
| pyro    | tabla | 200 | 0.63 | 0.83 | 0.64 | 2.78 | 48 |
| pyro    | tabla | 200 | 0.34 | 0.49 | 0.35 | 1.01 | 48 |
| pyro    | tabla | 200 | 0.3  | 0.39 | 0.32 | 1.27 | 48 |
```

Archivos generados: `semana11/laboratorio/mediciones.csv` y `semana12/laboratorio/mediciones.csv`.
