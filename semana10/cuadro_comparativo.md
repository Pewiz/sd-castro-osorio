# Cuadro comparativo — RMI, CORBA, DCOM y JSON-RPC

**Equipo:** Castro - Osorio  **Integrantes:** Felipe Castro, David Osorio  **Semana 10, trabajo autónomo**

Completen cada celda con una o dos frases propias (no copiar y pegar). Donde una tecnología no aplique, escriban "no aplica" y por qué.

| Criterio | Java RMI | CORBA | DCOM | JSON-RPC 2.0 |
|---|---|---|---|---|
| Año y origen (quién lo creó y para qué) | Lo creó Sun Microsystems en los años 90 para que un programa Java llame a objetos Java que están en otra máquina. | Lo creó el OMG, un grupo de empresas, desde 1991. Quería que objetos hechos en lenguajes distintos se pudieran llamar entre sí. | Lo creó Microsoft en 1996. Es COM (los componentes de Windows) pero funcionando por red. | Lo publicó el JSON-RPC Working Group en 2010. Es una especificación corta para llamar procedimientos remotos usando JSON. |
| Modelo (objetos remotos o procedimientos remotos) | Objetos remotos, con identidad y estado. | Objetos remotos, con identidad y estado. | Objetos remotos (componentes COM). | Procedimientos remotos. Cada llamada es independiente. |
| Contrato o IDL (cómo se declara la interfaz) | Una interfaz de Java que extiende `Remote`. No hay IDL aparte. | Un archivo IDL que no depende del lenguaje. | Un archivo IDL (MIDL) y una biblioteca de tipos. | No tiene IDL. El contrato queda escrito en la documentación, igual que nuestro protocolo.md. |
| Transporte y formato de los mensajes | Protocolo JRMP (también puede usar IIOP). Formato binario con la serialización de Java. | Protocolo IIOP sobre TCP. Formato binario. | Protocolo ORPC sobre el RPC de Microsoft. Formato binario. | Va sobre cualquier transporte, casi siempre HTTP. Formato texto (JSON). |
| Lenguajes y plataformas que soporta | Solo Java, en cualquier sistema que tenga la JVM. | Varios lenguajes, los que tengan un ORB. | Sobre todo Windows. | Cualquier lenguaje que pueda leer y escribir JSON. |
| Referencias remotas y estado (¿el servidor recuerda al cliente?) | Sí. El cliente guarda una referencia al objeto del servidor, y hay recolección de basura distribuida. | Sí. El cliente guarda una referencia al objeto del servidor. | Sí. El cliente tiene punteros a interfaces del servidor, y el servidor revisa cada cierto tiempo si el cliente sigue vivo. | No. El servidor no recuerda al cliente entre llamadas. El estado, si hay, lo maneja el programa. |
| Manejo de errores (cómo viaja un fallo al cliente) | Como excepción, por ejemplo `RemoteException`. | Como excepción, del sistema o definida en el IDL. | Como código de error (`HRESULT`). | Como un objeto `error` con `code`, `message` y `data`. |
| Relación con las cinco decisiones de la semana 9 (enmarcado, versión, id, errores, tipos) | La tecnología resuelve casi todo por el programador (enmarcado, ids y tipos). El programador casi no lo ve. | La resuelve el ORB con los mensajes de IIOP y los tipos del IDL. | También las resuelve la tecnología, con ORPC y los tipos de la biblioteca. | Resuelve versión (campo `jsonrpc`), id, errores y tipos (los de JSON). El enmarcado lo deja al transporte, o sea HTTP. |
| Estado actual (vigente, legado, reemplazado por qué) | Legado. Existe pero casi no se usa, porque solo sirve para Java. | Legado. Era muy complejo y lo reemplazaron los servicios web y REST. | Legado. Tenía problemas con los cortafuegos y lo reemplazaron .NET (WCF) y después gRPC y REST. | Vigente. Es simple y se sigue usando. |
| Caso de uso típico, real o histórico | Aplicaciones empresariales Java antiguas. | Sistemas grandes de empresas, como telecomunicaciones y bancos. | Aplicaciones antiguas de empresas que usaban Windows. | La API de los nodos de Ethereum y el Language Server Protocol de los editores de código. |

## Conclusión del equipo (5 a 8 líneas)

¿Cuál de las cuatro se parece más a lo que construyeron en la semana 9 y por qué? ¿Cuál elegirían hoy para un servicio interno y cuál para una API pública?

La que más se parece a lo que hicimos en la semana 9 es JSON-RPC. Nuestro mensaje con codec json ya tenía versión, id, operación, parámetros y error, y JSON-RPC tiene casi lo mismo con otros nombres. La diferencia es que JSON-RPC ya viene definido en una especificación y nosotros lo inventamos.
RMI, CORBA y DCOM trabajan con objetos remotos, y dejaron de usarse porque eran difíciles de usar y estaban atados a un lenguaje, a una plataforma o eran muy complejos.
Para un servicio interno elegiríamos JSON-RPC, porque es simple y nosotros controlamos los dos lados. Para una API pública también, porque cualquier lenguaje la puede usar con HTTP y JSON, y las otras tres piden software especial o tienen problemas con los cortafuegos.

## Fuentes consultadas

Mínimo tres, con formato autor, título, año y enlace.

1. Tanenbaum, A. y Van Steen, M. (2017). *Sistemas distribuidos, principios y paradigmas*. Capítulo 4, sección 4.2.
2. Coulouris, G. y otros (2001). *Sistemas Distribuidos. Conceptos y diseño*. Capítulo 5.
3. JSON-RPC Working Group (2010). *JSON-RPC 2.0 Specification*. https://www.jsonrpc.org/specification
4. Oracle. *Java RMI Tutorial*. https://docs.oracle.com
5. Object Management Group. *CORBA Specification*, introducción. https://www.omg.org
6. Microsoft Learn. *Component Object Model (COM)* y *DCOM*. https://learn.microsoft.com
