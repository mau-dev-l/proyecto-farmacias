# Auditoría del sistema contra los apartados del documento de la materia

Proyecto: **Sistema Web de Gestión de Inventarios y Control de Caducidades para la Reducción de Mermas en Farmacias Independientes de Tuxtla Gutiérrez, Chiapas**
Stack: Python + FastAPI (backend), React + Vite (frontend), PostgreSQL + pgvector, Ollama + LangChain, bot de Telegram (aiogram), APScheduler.

## Instrucciones para el agente

1. Revisa el sistema (código, base de datos, API, interfaces y pruebas) contra cada apartado de este archivo.
2. **No modifiques nada.** Solo reporta.
3. Para cada elemento indica uno de estos estados: **Cumple**, **Parcial**, **Falta** o **No verificable**, con la evidencia (archivo, ruta, tabla o pantalla) y una nota breve.
4. Al final entrega: (a) la lista de faltantes y parciales ordenada por prioridad, (b) cualquier elemento del sistema que no esté contemplado en este documento, y (c) cualquier contradicción entre este documento y la implementación.
5. Los valores marcados como "de diseño" son propuestas del equipo; si la implementación usa otros, repórtalo como diferencia, no como error.

---

## Apartados que pide el documento (a partir de Requisitos)

| # | Apartado solicitado | Qué pide |
|---|---|---|
| 3 | Requisitos funcionales y no funcionales | Considerar todos los requisitos funcionales y no funcionales del desarrollo |
| 4 | Casos de uso | Diagrama y documentación de cada caso de uso |
| 5 | Diseño de interfaces | Incluir todas las interfaces del software |
| 6 | Diagrama de componentes | Por componente: determinar la complejidad ciclomática, establecer las rutas para pruebas y aplicar el principio de Pareto |
| 7 | Pruebas de análisis de valores límite | a) Condiciones de entrada, tipo, clases de equivalencia válidas y no válidas. b) Diseño de pruebas |

---

## 3. Requisitos funcionales (verificar que cada uno esté implementado)

| ID | Módulo | Requisito |
|---|---|---|
| RF-01 | Usuarios y autenticación | Inicio de sesión para administradores y empleados |
| RF-02 | | Gestión de roles y permisos |
| RF-03 | Inventario | Alta, baja y modificación de medicamentos |
| RF-04 | | Consulta de existencias en tiempo real |
| RF-05 | | Actualización automática del stock |
| RF-06 | Código de barras | Registro de productos mediante escaneo |
| RF-07 | | Búsqueda rápida por código de barras |
| RF-08 | Lotes y caducidad | Registro de lotes y fechas de vencimiento |
| RF-09 | | Múltiples lotes por medicamento |
| RF-10 | | Seguimiento de productos próximos a vencer |
| RF-11 | Alertas | Notificaciones de productos próximos a caducar |
| RF-12 | | Alertas configurables por días de anticipación |
| RF-13 | | Identificación visual de productos vencidos |
| RF-14 | Kárdex | Registro de entradas y salidas |
| RF-15 | | Historial de movimientos por producto y lote |
| RF-16 | | Consulta de movimientos por fecha |
| RF-17 | PEPS | Sugerir la salida de los productos con caducidad más próxima |
| RF-18 | | Priorizar los lotes más antiguos |
| RF-19 | Reportes | Mermas por medicamentos caducados |
| RF-20 | | Productos próximos a vencer |
| RF-21 | | Inventario y movimientos |
| RF-22 | | Estadísticas de pérdidas económicas |
| RF-23 | API REST | Endpoints para consulta y actualización de inventarios |
| RF-24 | | Integración con otros sistemas si es necesario |
| RF-25 | Asistente de Telegram | Vinculación de la cuenta con código de un solo uso |
| RF-26 | | Consulta de existencias, próximos a vencer y alertas en lenguaje natural (el modelo solo redacta con datos de la API) |
| RF-27 | | Consulta del manual y políticas mediante RAG |

## 3. Requisitos no funcionales

| ID | Categoría | Requisito |
|---|---|---|
| RNF-01 | Rendimiento | Consultas de inventario en menos de 2 segundos |
| RNF-02 | | La API soporta consultas concurrentes sin degradación significativa |
| RNF-03 | Disponibilidad | Disponibilidad mínima del 99 % |
| RNF-04 | | Respaldos automáticos de la base de datos |
| RNF-05 | Seguridad | Contraseñas almacenadas cifradas (hash) |
| RNF-06 | | Funciones críticas controladas por roles |
| RNF-07 | | Comunicación mediante HTTPS |
| RNF-08 | Usabilidad | Interfaz intuitiva para personal sin conocimientos técnicos avanzados |
| RNF-09 | | El registro por código de barras reduce el tiempo de captura frente al manual |
| RNF-10 | Escalabilidad | Agregar sucursales o usuarios sin modificar la arquitectura |
| RNF-11 | Mantenibilidad | Arquitectura modular |
| RNF-12 | | API REST documentada (OpenAPI o Swagger) |
| RNF-13 | Compatibilidad | Navegadores modernos (Chrome, Edge y Firefox) |
| RNF-14 | | Compatible con lectores de códigos de barras comerciales |

**Preguntas para el agente:** ¿hay funcionalidad implementada que no esté en estas listas? ¿hay algún requisito sin implementar o sin forma de verificarse (por ejemplo respaldos automáticos, HTTPS, límite de 2 segundos)?

---

## 4. Casos de uso (16)

Actores: Administrador (hereda del Empleado), Empleado, Usuario de Telegram, Sistema programado, Servicio LLM (Ollama).

| ID | Caso de uso | Actor principal | Rol que puede ejecutarlo |
|---|---|---|---|
| CU-01 | Iniciar sesión (JWT, bloqueo tras 5 intentos fallidos) | Administrador, Empleado | Todos |
| CU-02 | Gestionar usuarios y roles | Administrador | Solo administrador |
| CU-03 | Gestionar sucursales | Administrador | Solo administrador |
| CU-04 | Gestionar medicamentos (la baja, solo administrador) | Administrador, Empleado | Todos |
| CU-05 | Buscar medicamento por código de barras | Empleado | Todos |
| CU-06 | Registrar entrada de lote | Empleado | Todos |
| CU-07 | Registrar salida (venta o merma) con PEPS | Empleado | Todos |
| CU-08 | Consultar existencias | Administrador, Empleado | Todos |
| CU-09 | Consultar kárdex | Administrador, Empleado | Todos |
| CU-10 | Configurar alertas de vencimiento | Administrador | Solo administrador |
| CU-11 | Generar alertas automáticas (tarea programada diaria) | Sistema programado | Sistema |
| CU-12 | Consultar próximos a vencer y vencidos | Administrador, Empleado | Todos |
| CU-13 | Generar reportes e indicadores (exportar PDF o CSV) | Administrador | Solo administrador |
| CU-14 | Vincular cuenta de Telegram | Administrador, Empleado | Todos |
| CU-15 | Consultar inventario por Telegram | Usuario de Telegram | Chat vinculado |
| CU-16 | Consultar manual y políticas por Telegram (RAG) | Usuario de Telegram | Chat vinculado |

Relaciones: CU-06 y CU-07 incluyen CU-05; CU-07 incluye la selección PEPS; CU-12 consulta las alertas de CU-11; CU-15 y CU-16 requieren el servicio LLM; todos excepto CU-01 requieren sesión.

**Reglas de negocio de los casos de uso que deben cumplirse**
- Entrada de lote: rechaza cantidad menor a 1, fecha de caducidad anterior a hoy y costo negativo; mismo lote con la misma caducidad suma cantidad; mismo lote con distinta caducidad responde conflicto (409).
- Salida: la venta excluye lotes vencidos; la merma los incluye; descuenta por lote con la caducidad más próxima primero, en una transacción con bloqueo de filas; registra un movimiento por lote; genera alerta de stock mínimo si la existencia vendible queda por debajo del mínimo.
- Kárdex: solo inserciones (inmutable); cada movimiento guarda el saldo del lote.
- Alertas: sin duplicados por lote, tipo y umbral; los lotes con caducidad anterior a hoy se marcan como vencidos.
- Telegram: código de un solo uso con vencimiento; un chat no puede vincularse a dos usuarios; el bot y el modelo nunca acceden a la base de datos, solo la API.

**Preguntas para el agente:** ¿cada caso de uso tiene su ruta de API, su pantalla y su regla implementadas? ¿Algún caso de uso falta, está incompleto o se ejecuta con un rol equivocado?

---

## 5. Interfaces (11)

| # | Interfaz | Casos de uso |
|---|---|---|
| 1 | Inicio de sesión | CU-01 |
| 2 | Panel general (indicadores, próximos a vencer, mermas del mes) | Resumen |
| 3 | Inventario (búsqueda o escaneo, filtro de sucursal, existencia, mínimo, lotes, estado) | CU-08 |
| 4 | Medicamentos (formulario y catálogo) | CU-04 |
| 5 | Entrada de lote | CU-05, CU-06 |
| 6 | Salida de producto (lotes sugeridos por PEPS, aviso de lote vencido) | CU-07 |
| 7 | Kárdex (filtros y movimientos) | CU-09 |
| 8 | Alertas (pestañas y configuración de días) | CU-10, CU-12 |
| 9 | Reportes (indicadores, gráfica y exportación PDF y CSV) | CU-13 |
| 10 | Administración (usuarios y sucursales) | CU-02, CU-03 |
| 11 | Telegram (código de vinculación y ejemplo de consulta) | CU-14, CU-15 |

Paleta: azul marino y verde azulado sobre fondos claros; verde, ámbar y rojo solo para estados.

**Preguntas para el agente:** ¿existe en el frontend cada una de estas pantallas? ¿Hay pantallas implementadas que no estén en la lista? ¿Se respeta el menú por rol (el empleado no ve reportes ni administración)?

---

## 6. Diagrama de componentes

Componentes propios: Frontend, Routers API REST, Servicios de negocio, Repositorios, Tarea programada, Módulo IA, Bot de Telegram. Externos o de infraestructura (no se analizan): PostgreSQL + pgvector, Ollama, Telegram API.

Para cada componente se analizó una función representativa: grafo de flujo, complejidad ciclomática V(G) = E − N + 2 = P + 1 y rutas independientes (conjunto básico de McCabe).

| Clave | Componente funcional | Función analizada | Módulo del diagrama | N | E | P | V(G) = rutas |
|---|---|---|---|---|---|---|---|
| FE | Captura de código de barras | `useBarcodeScanner.onKey` | Frontend | 9 | 11 | 3 | 4 |
| RT | Control de acceso por rol | `deps.require_role` | Routers API REST | 13 | 17 | 5 | 6 |
| AU | Autenticación | `auth_service.login` | Servicios de negocio | 15 | 19 | 5 | 6 |
| EN | Entrada de lote | `inventory_service.registrar_entrada` | Servicios de negocio | 17 | 22 | 6 | 7 |
| SA | Salida con PEPS | `peps_service.registrar_salida` | Servicios de negocio | 19 | 24 | 6 | 7 |
| TG | Vinculación de Telegram | `telegram_service.vincular` | Servicios de negocio | 14 | 18 | 5 | 6 |
| RP | Consulta de lotes para PEPS | `lote_repository.lotes_peps` | Repositorios | 8 | 9 | 2 | 3 |
| AL | Generación de alertas | `alert_service.evaluar_lote` | Tarea programada | 12 | 16 | 5 | 6 |
| IA | Respuesta del asistente | `agent.responder` | Módulo IA | 21 | 27 | 7 | 8 |
| BT | Manejo de mensajes del bot | `bot.manejar_mensaje` | Bot de Telegram | 13 | 16 | 4 | 5 |

Complejidad total: 58.

**Principio de Pareto (por complejidad ciclomática, como indicador de riesgo)**

| Orden | Componente | V(G) | % | % acumulado | Prioridad de pruebas |
|---|---|---|---|---|---|
| 1 | IA | 8 | 13.8 | 13.8 | Alta |
| 2 | SA | 7 | 12.1 | 25.9 | Alta |
| 3 | EN | 7 | 12.1 | 37.9 | Alta |
| 4 | AU | 6 | 10.3 | 48.3 | Alta |
| 5 | RT | 6 | 10.3 | 58.6 | Media |
| 6 | AL | 6 | 10.3 | 69.0 | Media |
| 7 | TG | 6 | 10.3 | 79.3 | Media |
| 8 | BT | 5 | 8.6 | 87.9 | Normal |
| 9 | FE | 4 | 6.9 | 94.8 | Normal |
| 10 | RP | 3 | 5.2 | 100.0 | Normal |

Prioridad alta hasta el 50 % acumulado, media hasta el 80 %, normal el resto. La complejidad está repartida de forma pareja, por eso se usan tres niveles.

**Estructura lógica de cada función (para comprobar que el código la respeta)**
- **FE:** si el intervalo entre teclas es mayor a 50 ms, reinicia el buffer; con Enter y 8 o más caracteres emite el código; con Enter y menos de 8 lo descarta con aviso.
- **RT:** token ausente, con firma alterada o expirado responde 401; usuario inactivo o rol no permitido responde 403; en otro caso concede el acceso.
- **AU:** correo inexistente 401; usuario inactivo 403; cuenta bloqueada 423; contraseña incorrecta suma un intento y al llegar a 5 bloquea la cuenta 15 minutos; contraseña correcta reinicia intentos y emite JWT.
- **EN:** medicamento inexistente 404; cantidad menor a 1, fecha menor a hoy o costo negativo 400; lote existente con distinta caducidad 409; en otro caso crea o suma al lote y registra el movimiento ENTRADA.
- **SA:** cantidad menor a 1 400; medicamento inexistente 404; existencia insuficiente 400; recorre los lotes por caducidad y descuenta lote por lote; si la existencia vendible queda menor al mínimo genera alerta STOCK_MINIMO.
- **TG:** código inexistente 404; usado 400; expirado 400; chat vinculado a otro usuario 409; si el usuario ya tiene vínculo reemplaza el chat, si no crea uno.
- **RP:** consulta lotes con existencia por caducidad con `FOR UPDATE`, con o sin vencidos según el indicador.
- **AL:** lote sin existencia no genera alerta; vencido se marca VENCIDO y crea alerta VENCIDO una sola vez; en otro caso aplica el menor umbral que cubre los días restantes y crea la alerta una sola vez.
- **IA:** chat no vinculado 401; pregunta vacía 400; modelo no disponible 503; intención no soportada responde fuera de alcance; manual con fragmentos de similitud 0.70 o más responde con el contexto; inventario llama a la herramienta (endpoint de la API) y redacta con sus datos.
- **BT:** mensaje sin texto, aviso; `/vincular` envía el código a la API; otro texto se reenvía a la API; error o más de 30 s responde error temporal.

**Preguntas para el agente:** ¿el código implementa estas funciones con esa lógica? ¿Existen funciones con lógica de decisión relevante que no estén analizadas (por ejemplo reportes o exportación)? Si se mide con `radon cc`, ¿coinciden los valores? (Radon suma cada `and` y `or`, así que una diferencia puede deberse a condiciones compuestas.)

---

## 7. Pruebas de valores límite

Requisito del documento: a) establecer condiciones de entrada, tipo, clases de equivalencia válidas y no válidas; b) diseño de pruebas.

Dos niveles de prueba: **servicio** (rutas del grafo, respuestas 400, 403, 404, 409, 423) y **esquema de validación de la API** (tipo, formato, longitud y rango, respuesta 422).

**Valores de diseño usados**

| Concepto | Valor |
|---|---|
| Bloqueo de cuenta | 15 minutos al quinto intento fallido |
| Cantidad por captura | 1 a 99,999 |
| Costo unitario | 0.00 a 99,999,999.99, dos decimales |
| Longitudes máximas | correo 150, número de lote 50, código de barras 30, código de vinculación 10 |
| Umbrales de alerta | 90, 60 y 30 días |
| Lote vencido | fecha de caducidad anterior a la fecha actual |
| Lector de barras | pausa mayor a 50 ms reinicia el buffer; mínimo 8 caracteres |
| Pregunta al asistente | 1 a 500 caracteres |
| RAG | fragmento relevante con similitud 0.70 o más |
| Bot | tiempo de espera de la API de 30 segundos |

**Entradas con valores límite por componente**

| Clave | Entradas y límites |
|---|---|
| FE | Intervalo entre teclas: 50 y 51 ms. Longitud del código: 0, 7, 8, 30 y 31 caracteres |
| RT | Token ausente, con firma alterada, expirado (`exp` = ahora y ahora − 1 s); usuario activo e inactivo; rol permitido y no permitido |
| AU | Correo: 0, 1, 150 y 151 caracteres, sin arroba. Intentos previos: 3 y 4. Bloqueo: `bloqueado_hasta` = ahora y ahora + 1 s |
| EN | Cantidad: 0, 1, 99,999 y 100,000. Fecha: hoy − 1, hoy y hoy + 1, y 31/02. Costo: −0.01, 0.00, 99,999,999.99 y 100,000,000.00. Lote: 0, 1, 50 y 51 caracteres. Lote existente con la misma y con distinta caducidad |
| SA | Cantidad: 0, 1, N − 1, N y N + 1 (N = existencia vendible). Existencia restante frente al mínimo M: M y M − 1. Tipo: VENTA, MERMA y otro valor |
| TG | Código: 0, 1, 10 y 11 caracteres. Vencimiento: ahora = vencimiento y vencimiento + 1 s. Código usado; chat ya vinculado; usuario con y sin vínculo previo |
| RP | Incluir vencidos sí y no; caducidad = hoy y hoy − 1; lotes con existencia 0 |
| AL | Días restantes: −1, 0, 30, 31, 60, 61, 90 y 91. Existencia 0 y 1. Umbral configurado 0 y 1. Alerta previa existente y no existente |
| IA | Pregunta: 0, 1, 500 y 501 caracteres. Similitud: 0.69 y 0.70. Chat vinculado y no vinculado. Modelo disponible y no disponible. Con y sin resultados |
| BT | Mensaje con y sin texto. `/vincular` con código válido e inválido. Respuesta de la API a los 30 y a los 31 segundos |

**Preguntas para el agente:** ¿existen pruebas automatizadas (pytest) para cada límite? ¿Las validaciones de esquema (Pydantic) y de servicio coinciden con los valores de diseño? ¿Qué límites no están cubiertos por ninguna prueba?

---

## Anexo. Inventario de rutas de la API (25) para contrastar con el código

Prefijo `/api/v1`. A = Administrador, E = Empleado (incluye al administrador), Bot = servicio del bot.

| Método | Ruta | Rol |
|---|---|---|
| POST | `/auth/login` | Público |
| GET | `/auth/me` | A, E |
| GET, POST | `/usuarios` | A |
| PUT, PATCH | `/usuarios/{id}` | A |
| GET, POST, PUT | `/sucursales` | A |
| GET | `/medicamentos?q=&page=` | A, E |
| GET | `/medicamentos/barcode/{codigo}` | A, E |
| POST, PUT | `/medicamentos` | A, E |
| DELETE | `/medicamentos/{id}` (baja lógica) | A |
| GET | `/inventario?sucursal_id=&q=` | A, E |
| GET | `/medicamentos/{id}/lotes` | A, E |
| POST | `/movimientos/entrada` | A, E |
| POST | `/movimientos/salida` | A, E |
| GET | `/movimientos/peps-sugerido?medicamento_id=&cantidad=` | A, E |
| GET | `/kardex?medicamento_id=&lote_id=&desde=&hasta=` | A, E |
| GET | `/alertas?tipo=&leida=` | A, E |
| PATCH | `/alertas/{id}/leida` | A, E |
| GET, PUT | `/alertas/configuracion` | A |
| GET | `/reportes/mermas?desde=&hasta=` | A |
| GET | `/reportes/proximos-vencer?dias=` | A |
| GET | `/reportes/inventario` | A |
| GET | `/reportes/dashboard` | A |
| POST | `/telegram/codigo` | A, E |
| POST | `/telegram/vincular` | Bot |
| POST | `/bot/consulta` | Bot |

Tablas de la base de datos (12): sucursales, usuarios, medicamentos, proveedores, lotes, movimientos, configuracion_alertas, alertas, telegram_vinculos, codigos_vinculacion, documentos_rag, consultas_bot.

---

## Formato de respuesta esperado del agente

1. **Resumen:** una línea por apartado (3 a 7) con el estado general.
2. **Tabla de hallazgos:** elemento, estado (Cumple, Parcial, Falta o No verificable), evidencia, nota.
3. **Faltantes y parciales por prioridad.**
4. **Elementos en el sistema que no están en este documento.**
5. **Contradicciones entre este documento y la implementación.**
