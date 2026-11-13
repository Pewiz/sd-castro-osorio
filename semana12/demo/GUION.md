# Guion de la demo del jueves 12-11 (docente)

Misma base que `laboratorio/`. Abrir tres terminales en `semana12/demo/`.
En las tres, `alias c='docker compose exec cliente'` (PowerShell
`function c { docker compose exec cliente @args }`).

En bash se puede cambiar una variable solo para un comando (`MODO=percall docker compose up -d servidor`),
que es lo que usa este guion. En PowerShell eso no existe, ahí se edita el valor en `.env` y se ejecuta
`docker compose up -d servidor`, y para volver se restaura el valor en `.env`.

Después de recrear o reiniciar el servidor, esperar un par de segundos antes de llamar al cliente,
porque el contenedor tarda en volver a escuchar.

## Antes de la clase

```bash
docker compose up -d --build
c python cliente_pyro.py listar        # debe responder stock {}
```

## Parte A, del procedimiento al objeto (Bloque 1)

```bash
docker compose logs servidor                 # 1. URI PYRO:inventario@servidor:9100 y registro
c python cliente_pyro.py uri                 # 2. nombre lógico -> URI
c python cliente_pyro.py agregar cafe 10
c python cliente_pyro.py agregar te 5
c python cliente_pyro.py pedido cafe:2 te:1  # 3. llega un Proxy, URI obj_... , y al final referencia colgante
c python cliente_pyro.py listar              # el stock bajó
POR_VALOR=1 docker compose up -d servidor    # 4. experimento por valor
c python cliente_pyro.py agregar cafe 5
c python cliente_pyro.py pedido cafe:1       # ERROR de serialización, objetos.Pedido
docker compose up -d servidor                # vuelve a la normalidad (POR_VALOR=0)
```

## Parte B, ciclo de vida y fallas (Bloque 2)

```bash
MODO=percall docker compose up -d servidor ; c python cliente_pyro.py quien --veces 2
MODO=session docker compose up -d servidor ; c python cliente_pyro.py quien --veces 2
docker compose up -d servidor                # single otra vez
c python cliente_pyro.py quien --veces 2

c python cliente_pyro.py agregar cafe 3
c python cliente_pyro.py pedido cafe:99      # falla el dominio, el pedido queda vivo
c python cliente_pyro.py pedido cafe:99
c python cliente_pyro.py vivos               # 2 pedidos huérfanos, nadie los borra
```

Falla provocada, con tres terminales

```bash
# terminal 2
c python cliente_pyro.py vigilar
# terminal 3
c python cliente_pyro.py agregar cafe 10
c python cliente_pyro.py pedido cafe:1 --esperar 20
# terminal 1, mientras el pedido espera
docker compose kill servidor                 # vigilar muestra FALLA
docker compose start servidor                # vigilar vuelve, stock {} (estado perdido)
                                             # terminal 3 termina en referencia colgante
docker compose kill nombres                  # vigilar SIGUE funcionando
c python cliente_pyro.py listar              # cliente nuevo, no encuentra el servidor de nombres
docker compose start nombres
c python cliente_pyro.py listar              # unknown name, el registro se perdió
docker compose restart servidor              # se vuelve a registrar al arrancar
c python cliente_pyro.py listar              # ok
```

## Después

```bash
docker compose down -v
```
