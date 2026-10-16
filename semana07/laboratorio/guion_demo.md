# Guion de la demostración — Evaluación 3 (viernes 16-10)

Equipo Castro - Osorio. Carpeta: `semana07/laboratorio`.


| Minuto | Qué                           | Quién          |
| ------ | ----------------------------- | -------------- |
| 0 a 2  | `diagramas/despliegue_v2.png` | David          |
| 2 a 4  | Protocolo HTTP                | David          |
| 4 a 5  | Contenedores                  | Felipe         |
| 5 a 6  | Carga                         | Felipe         |
| 6 a 9  | Falla                         | Felipe y David |


## Antes

```powershell
cd semana07\laboratorio
docker compose up -d --build
docker compose ps
docker compose exec cliente python cliente_http.py GET /jugadores
```



## 2:00 — protocolo

```powershell
docker compose exec cliente python cliente_http.py GET /jugadores
docker compose exec cliente python cliente_http.py POST /jugadores jugador=ana
docker compose exec cliente python cliente_http.py POST /jugadores jugador=ana
```

`200` tabla en 0. `201` ana. `409` `JUGADOR_YA_EXISTE`.

## 4:00 — contenedores

```powershell
docker compose ps
```



## 5:00 — carga

```powershell
docker compose exec cliente python cliente_http.py --repetir 100 --paralelo 10 POST /jugadores/felipe/puntos puntos=1
docker compose exec cliente python cliente_http.py GET /jugadores/felipe
```

`{201: 100}`, repartido entre `api1` y `api2`. GET: `"puntos": 100`.

## 6:00 — falla

```powershell
docker compose kill api1
docker compose exec cliente python cliente_http.py GET /jugadores
docker compose exec cliente python cliente_http.py GET /jugadores
```

Uno de los dos GET tarda cerca de `1 s` y responde `200` con `"replica": "api2"`. `felipe` sigue en 100.

```powershell
docker compose kill servidor
docker compose exec cliente python cliente_http.py GET /jugadores
```

`503` `SERVIDOR_NO_DISPONIBLE`.

```powershell
docker compose up -d servidor
docker compose exec cliente python cliente_http.py GET /jugadores
```

`200`. `david:0` `felipe:0`.