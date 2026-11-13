# Semana 12, objetos distribuidos con Pyro5

El dominio (`dominio.py`) es el mismo de la semana 11. Lo que cambia es la forma
de exponerlo, ahora como objetos remotos que viven en el nodo `servidor`.

| Archivo | Qué es |
|---|---|
| `dominio.py` | Reglas del negocio, igual que en `semana11/`. Reemplácenlo por el suyo |
| `objetos.py` | Clases expuestas `Inventario` (entrada) y `Pedido` (objeto con estado, viaja por referencia) |
| `servidor_pyro.py` | Daemon de Pyro5, registra `Inventario` en el servidor de nombres |
| `cliente_pyro.py` | Cliente de línea de comandos con `uri`, `listar`, `agregar`, `quitar`, `quien`, `pedido`, `vivos` y `vigilar` |
| `docker-compose.yml` | Nodos `nombres`, `servidor` y `cliente` en la red `sd_net` |
| `.env` | Configuración (`EQUIPO`, `MODO`, `POR_VALOR`, `REREGISTRO`). Es un archivo oculto |
| `observaciones.md` | Registro del taller, se entrega hoy antes de las 16.00 |
| `calidad.md` | Lista de verificación antes del push |

## Levantar y probar

```bash
docker compose up -d --build
docker compose exec cliente python cliente_pyro.py uri
docker compose exec cliente python cliente_pyro.py pedido cafe:2
```

Con el alias del curso (`alias c='docker compose exec cliente'`) queda `c python cliente_pyro.py listar`.

## Variables

| Variable | Valor por defecto | Para qué |
|---|---|---|
| `EQUIPO` | `referencia` | Nombre lógico `sd.<EQUIPO>.inventario` |
| `MODO` | `single` | Modo de instancia del `Inventario` (`single`, `session`, `percall`) |
| `POR_VALOR` | `0` | Con `1`, la fábrica devuelve el objeto sin registrarlo (experimento) |
| `REREGISTRO` | `0` | Segundos entre re-registros en el servidor de nombres, `0` es nunca |

Los valores se cambian en el archivo `.env` de esta carpeta (por ejemplo `MODO=session`) y después
se ejecuta `docker compose up -d servidor`. Así funciona igual en bash y en PowerShell, y las tres
terminales del paso 5 ven la misma configuración. Para volver, se restaura el valor en `.env` y se
repite el comando.

## Sin Docker

```bash
pip install -r requirements.txt
export NOMBRES_HOST=127.0.0.1 SERVIDOR_HOST=127.0.0.1
python -m Pyro5.nameserver -n 127.0.0.1 -p 9090 -x     # terminal 1
python servidor_pyro.py                                 # terminal 2
python cliente_pyro.py listar                           # terminal 3
```

En PowerShell las variables se definen con `$env:NOMBRES_HOST="127.0.0.1"`.
