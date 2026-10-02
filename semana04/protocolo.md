# Protocolo de aplicación — Equipo ______

Versión 0.1 · semana 4 · Este archivo evoluciona cada semana junto con el servicio.

## 1. Transporte

- Protocolo de transporte: TCP
- Puerto del servidor: 5000
- Codificación: UTF-8
- Delimitador de mensaje: una línea terminada en `\n`
- Quién inicia: el cliente. El servidor solo responde.

## 2. Mensajes

Completen la tabla. Una fila por comando. La operación propia del equipo va al final.

| Comando (cliente → servidor) | Argumentos | Respuesta (servidor → cliente) | ¿Cambia el estado de la conexión? |
|---|---|---|---|
| `HOLA <nombre>` | nombre, texto libre | `OK hola <nombre>` | Sí, guarda el nombre |
| `ECO <texto>` | | | |
| `CONTAR` | | | |
| `SALIR` | | | |
| (cualquier otro) | | `ERROR comando desconocido` | |
| `______` (operación propia) | | | |

## 3. Estado

- ¿Qué recuerda el servidor de cada conexión? ______
- ¿Qué pasa con ese estado cuando el cliente se desconecta? ______
- Si el servidor se reinicia mientras un cliente está conectado, ¿qué pierde el cliente? ______

## 4. Secuencia típica

Dibujen o describan una sesión completa, desde `connect` hasta `ADIOS`.

```
cliente                servidor
   |---- connect --------->|
   |---- HOLA equipo ----->|
   |<--- OK hola equipo ---|
   |         ...           |
   |---- SALIR ----------->|
   |<--- ADIOS ------------|
   |         (cierre)      |
```

## 5. Errores

| Situación | Qué ve el cliente | Qué ve el servidor |
|---|---|---|
| Comando desconocido | `ERROR comando desconocido` | log con el comando |
| Servidor caído durante la sesión | | |
| Cliente sin red durante la sesión | | |
| Cliente corta sin `SALIR` (Ctrl+C) | | |
