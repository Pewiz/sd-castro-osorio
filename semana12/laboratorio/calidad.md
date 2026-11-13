# Lista de calidad antes del push (semana 12)

Marquen con una x lo que cumplen. Lo que quede sin marcar va como pendiente en la bitácora.

- [ ] Cada clase expuesta tiene docstring que dice para qué sirve
- [ ] Cada método expuesto tiene docstring que dice si cambia estado o no
- [ ] `dominio.py` es el mismo de la semana 11, no se modificó para Pyro5
- [ ] El cliente captura `CommunicationError` y `NamingError` y muestra un mensaje entendible
- [ ] Las excepciones propias del dominio llegan al cliente con su nombre (registradas con `register_dict_to_class`)
- [ ] El objeto con estado se desregistra al terminar su vida (confirmar o cancelar)
- [ ] No hay direcciones IP escritas en el código, todo sale de variables de entorno
- [ ] `README.md` de `semana12/` explica cómo levantar y probar en tres comandos
- [ ] `observaciones.md` tiene los cinco pasos completos
