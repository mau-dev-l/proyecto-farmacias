# Diseño técnico: Sistema Web de Inventarios y Control de Caducidades para Farmacias Independientes

Stack: Python + FastAPI (backend), React + Vite (frontend), PostgreSQL (BD), Ollama + LangChain + Telegram (asistente).

## 1. Casos de uso

### 1.1 Actores

| Actor | Descripción |
| --- | --- |
| Administrador | Gestiona usuarios, sucursales, configuración y reportes. Hereda todo lo del Empleado. |
| Empleado | Opera el inventario: escaneo, entradas, salidas, consultas. |
| Usuario de Telegram | Administrador o Empleado con cuenta vinculada que consulta mediante el bot. |
| Sistema (Scheduler) | Actor secundario que genera alertas automáticas de forma periódica. |
| Servicio LLM (Ollama) | Actor secundario que interpreta la consulta y redacta la respuesta. |

### 1.2 Catálogo de casos de uso

| ID | Caso de uso | Actor principal |
| --- | --- | --- |
| CU-01 | Iniciar sesión | Administrador, Empleado |
| CU-02 | Gestionar usuarios y roles | Administrador |
| CU-03 | Gestionar sucursales | Administrador |
| CU-04 | Gestionar medicamentos | Administrador, Empleado |
| CU-05 | Buscar medicamento por código de barras | Empleado |
| CU-06 | Registrar entrada de lote | Empleado |
| CU-07 | Registrar salida (venta o merma) con PEPS | Empleado |
| CU-08 | Consultar existencias | Administrador, Empleado |
| CU-09 | Consultar kárdex | Administrador, Empleado |
| CU-10 | Configurar alertas de vencimiento | Administrador |
| CU-11 | Generar alertas automáticas | Sistema |
| CU-12 | Consultar productos próximos a vencer y vencidos | Administrador, Empleado |
| CU-13 | Generar reportes e indicadores | Administrador |
| CU-14 | Vincular cuenta de Telegram | Administrador, Empleado |
| CU-15 | Consultar inventario por Telegram | Usuario de Telegram |
| CU-16 | Consultar manual y políticas por Telegram (RAG) | Usuario de Telegram |

Relaciones: CU-06 y CU-07 incluyen CU-05 (búsqueda por código). CU-07 incluye la selección PEPS. CU-12 extiende a CU-11 (consume las alertas generadas). CU-15 y CU-16 incluyen la intervención del Servicio LLM. Todos, excepto CU-01, incluyen la validación de sesión (CU-01).

&#91;embedded content: diagrama de casos de uso · 5 actores, 16 casos\]

El administrador es una especialización del empleado, por eso hereda todos sus casos de uso.

### 1.3 Documentación de cada caso de uso

**CU-01 Iniciar sesión**

- Precondición: usuario registrado y activo.
- Flujo principal: 1) Ingresa correo y contraseña. 2) El sistema valida credenciales. 3) Emite token JWT con rol. 4) Redirige al panel.
- Alternos: A1 credenciales inválidas, muestra error y cuenta intento. A2 usuario inactivo, acceso denegado. A3 5 intentos fallidos, bloqueo temporal.
- Postcondición: sesión activa con permisos según rol.

**CU-02 Gestionar usuarios y roles**

- Precondición: sesión de Administrador.
- Flujo principal: 1) Abre módulo de usuarios. 2) Crea o edita usuario (nombre, correo, rol, sucursal). 3) El sistema valida y guarda la contraseña cifrada. 4) Confirma.
- Alternos: A1 correo duplicado. A2 desactivar usuario en lugar de borrarlo. A3 no puede quitarse su propio rol de administrador.
- Postcondición: usuario creado, modificado o desactivado.

**CU-03 Gestionar sucursales**

- Precondición: sesión de Administrador.
- Flujo principal: 1) Registra o edita sucursal (nombre, dirección). 2) El sistema guarda. 3) Asigna usuarios a la sucursal.
- Alternos: A1 nombre duplicado. A2 sucursal con movimientos solo se puede desactivar.
- Postcondición: sucursal disponible para operar.

**CU-04 Gestionar medicamentos**

- Precondición: sesión activa.
- Flujo principal: 1) Elige alta, modificación o baja. 2) Captura nombre, sustancia activa, presentación, código de barras, stock mínimo, precio. 3) El sistema valida y guarda.
- Alternos: A1 código de barras ya existente. A2 baja lógica si tiene historial de movimientos. A3 campos obligatorios vacíos.
- Postcondición: catálogo actualizado.

**CU-05 Buscar medicamento por código de barras**

- Precondición: sesión activa; lector comercial conectado (entra como teclado).
- Flujo principal: 1) Escanea el código. 2) El sistema busca el medicamento. 3) Muestra datos, existencias y lotes.
- Alternos: A1 código no registrado, ofrece darlo de alta (CU-04). A2 lectura incompleta, solicita reintentar.
- Postcondición: medicamento identificado y seleccionado.

**CU-06 Registrar entrada de lote**

- Precondición: medicamento existente (CU-05).
- Flujo principal: 1) Escanea el producto. 2) Captura número de lote, fecha de caducidad, cantidad y costo. 3) El sistema valida. 4) Crea o actualiza el lote. 5) Registra movimiento de entrada en el kárdex y actualiza el stock.
- Alternos: A1 fecha de caducidad vencida o anterior a hoy, rechaza. A2 cantidad menor a 1. A3 lote ya existente con misma caducidad, suma cantidad. A4 mismo lote con distinta caducidad, error.
- Postcondición: existencias y kárdex actualizados.

**CU-07 Registrar salida (venta o merma) con PEPS**

- Precondición: medicamento con existencias.
- Flujo principal: 1) Escanea el producto e indica cantidad y tipo (venta o merma). 2) El sistema selecciona lotes por fecha de caducidad más próxima (PEPS). 3) Descuenta por lote. 4) Registra movimientos y actualiza stock. 5) Si el stock queda bajo el mínimo, genera alerta.
- Alternos: A1 stock insuficiente, rechaza. A2 el lote sugerido está vencido, bloquea venta y ofrece registrarlo como merma. A3 el usuario elige otro lote, exige motivo.
- Postcondición: salida registrada por lote con trazabilidad.

**CU-08 Consultar existencias**

- Flujo principal: 1) Abre inventario. 2) Filtra por nombre, código o sucursal. 3) El sistema muestra stock total y desglose por lote.
- Alternos: A1 sin resultados.
- Postcondición: ninguna (solo lectura).

**CU-09 Consultar kárdex**

- Flujo principal: 1) Selecciona medicamento y, opcionalmente, lote o rango de fechas. 2) El sistema lista entradas, salidas y saldo.
- Alternos: A1 sin movimientos en el rango.
- Postcondición: ninguna (solo lectura).

**CU-10 Configurar alertas de vencimiento**

- Precondición: sesión de Administrador.
- Flujo principal: 1) Define días de anticipación (por ejemplo 90, 60, 30). 2) El sistema valida y guarda.
- Alternos: A1 valor menor a 1 o no numérico, rechaza.
- Postcondición: configuración vigente para el CU-11.

**CU-11 Generar alertas automáticas**

- Actor: Sistema (tarea diaria programada).
- Flujo principal: 1) Se ejecuta el job. 2) Busca lotes con stock cuya caducidad entra en el umbral. 3) Crea alertas nuevas sin duplicar. 4) Marca lotes ya vencidos como vencidos.
- Alternos: A1 falla de BD, reintenta y registra el error.
- Postcondición: alertas disponibles en el panel y en Telegram.

**CU-12 Consultar productos próximos a vencer y vencidos**

- Flujo principal: 1) Abre el panel de alertas. 2) Filtra por estado (próximo o vencido). 3) El sistema muestra lotes con indicador visual. 4) Puede marcar alertas como leídas.
- Alternos: A1 sin alertas pendientes.
- Postcondición: alertas leídas actualizadas.

**CU-13 Generar reportes e indicadores**

- Precondición: sesión de Administrador.
- Flujo principal: 1) Elige tipo de reporte (mermas, próximos a vencer, inventario, movimientos) y rango. 2) El sistema calcula. 3) Muestra tablas y gráficas. 4) Exporta a PDF o CSV.
- Alternos: A1 rango inválido (fin anterior a inicio). A2 sin datos.
- Postcondición: reporte generado.

**CU-14 Vincular cuenta de Telegram**

- Precondición: sesión activa en la web.
- Flujo principal: 1) Solicita código de vinculación. 2) El sistema genera código de un solo uso con expiración. 3) El usuario lo envía al bot. 4) El bot valida y guarda el chat\_id.
- Alternos: A1 código expirado o usado. A2 chat ya vinculado a otro usuario.
- Postcondición: chat de Telegram autorizado.

**CU-15 Consultar inventario por Telegram**

- Precondición: cuenta vinculada (CU-14).
- Flujo principal: 1) Envía una pregunta (por ejemplo, qué vence este mes). 2) El bot pasa el texto al LLM (LangChain). 3) El LLM elige la herramienta y llama al endpoint de la API con el token del usuario. 4) La API consulta la BD y devuelve datos. 5) El LLM redacta la respuesta. 6) El bot la envía.
- Alternos: A1 chat no vinculado, rechaza. A2 consulta fuera de alcance, el bot lo indica. A3 LLM no disponible, responde con mensaje de error. A4 sin resultados.
- Postcondición: respuesta entregada; consulta registrada en bitácora.

**CU-16 Consultar manual y políticas por Telegram (RAG)**

- Precondición: documentos indexados en la base vectorial.
- Flujo principal: 1) Envía una pregunta sobre uso del sistema o políticas. 2) Se recuperan los fragmentos más similares. 3) El LLM redacta la respuesta con ese contexto.
- Alternos: A1 sin fragmentos relevantes, el bot indica que no tiene información.
- Postcondición: respuesta entregada.

## 2. Modelo de base de datos (PostgreSQL)

### 2.1 Tablas

| Tabla | Propósito |
| --- | --- |
| sucursales | Farmacias o sucursales (escalabilidad) |
| usuarios | Cuentas con rol y sucursal |
| medicamentos | Catálogo con código de barras único |
| proveedores | Origen de las entradas (opcional) |
| lotes | Lote, caducidad y existencia por medicamento y sucursal |
| movimientos | Kárdex, solo inserciones |
| configuracion\_alertas | Días de anticipación por sucursal |
| alertas | Alertas generadas por lote |
| telegram\_vinculos | Relación usuario y chat de Telegram |
| codigos\_vinculacion | Códigos de un solo uso para vincular |
| documentos\_rag | Fragmentos y embeddings (pgvector) |
| consultas\_bot | Bitácora de consultas del asistente |

### 2.2 Script SQL

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TYPE rol_usuario AS ENUM ('ADMIN','EMPLEADO');
CREATE TYPE tipo_movimiento AS ENUM ('ENTRADA','SALIDA_VENTA','SALIDA_MERMA','AJUSTE');
CREATE TYPE estado_lote AS ENUM ('ACTIVO','AGOTADO','VENCIDO');
CREATE TYPE tipo_alerta AS ENUM ('PROXIMO_VENCER','VENCIDO','STOCK_MINIMO');

CREATE TABLE sucursales (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL UNIQUE,
  direccion VARCHAR(255),
  activa BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE usuarios (
  id SERIAL PRIMARY KEY,
  sucursal_id INT NOT NULL REFERENCES sucursales(id),
  nombre VARCHAR(120) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  rol rol_usuario NOT NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  intentos_fallidos INT NOT NULL DEFAULT 0,
  bloqueado_hasta TIMESTAMPTZ,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE proveedores (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(150) NOT NULL,
  telefono VARCHAR(20)
);

CREATE TABLE medicamentos (
  id SERIAL PRIMARY KEY,
  codigo_barras VARCHAR(30) NOT NULL UNIQUE,
  nombre VARCHAR(150) NOT NULL,
  sustancia_activa VARCHAR(150),
  presentacion VARCHAR(100),
  precio_venta NUMERIC(10,2) NOT NULL CHECK (precio_venta >= 0),
  stock_minimo INT NOT NULL DEFAULT 0 CHECK (stock_minimo >= 0),
  activo BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX ix_med_nombre ON medicamentos (lower(nombre));

CREATE TABLE lotes (
  id SERIAL PRIMARY KEY,
  medicamento_id INT NOT NULL REFERENCES medicamentos(id),
  sucursal_id INT NOT NULL REFERENCES sucursales(id),
  proveedor_id INT REFERENCES proveedores(id),
  numero_lote VARCHAR(50) NOT NULL,
  fecha_caducidad DATE NOT NULL,
  cantidad_actual INT NOT NULL CHECK (cantidad_actual >= 0),
  costo_unitario NUMERIC(10,2) NOT NULL CHECK (costo_unitario >= 0),
  estado estado_lote NOT NULL DEFAULT 'ACTIVO',
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (medicamento_id, sucursal_id, numero_lote)
);
CREATE INDEX ix_lotes_peps ON lotes (medicamento_id, sucursal_id, fecha_caducidad)
  WHERE cantidad_actual > 0;

CREATE TABLE movimientos (
  id BIGSERIAL PRIMARY KEY,
  lote_id INT NOT NULL REFERENCES lotes(id),
  usuario_id INT NOT NULL REFERENCES usuarios(id),
  tipo tipo_movimiento NOT NULL,
  cantidad INT NOT NULL CHECK (cantidad > 0),
  saldo_lote INT NOT NULL CHECK (saldo_lote >= 0),
  costo_unitario NUMERIC(10,2) NOT NULL,
  motivo VARCHAR(255),
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_mov_lote_fecha ON movimientos (lote_id, creado_en);
CREATE INDEX ix_mov_fecha ON movimientos (creado_en);

CREATE TABLE configuracion_alertas (
  id SERIAL PRIMARY KEY,
  sucursal_id INT NOT NULL REFERENCES sucursales(id),
  dias_anticipacion INT NOT NULL CHECK (dias_anticipacion >= 1),
  UNIQUE (sucursal_id, dias_anticipacion)
);

CREATE TABLE alertas (
  id BIGSERIAL PRIMARY KEY,
  lote_id INT NOT NULL REFERENCES lotes(id),
  tipo tipo_alerta NOT NULL,
  dias_umbral INT,
  leida BOOLEAN NOT NULL DEFAULT FALSE,
  creada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (lote_id, tipo, dias_umbral)
);

CREATE TABLE telegram_vinculos (
  id SERIAL PRIMARY KEY,
  usuario_id INT NOT NULL UNIQUE REFERENCES usuarios(id),
  chat_id BIGINT NOT NULL UNIQUE,
  vinculado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE codigos_vinculacion (
  id SERIAL PRIMARY KEY,
  usuario_id INT NOT NULL REFERENCES usuarios(id),
  codigo VARCHAR(10) NOT NULL UNIQUE,
  expira_en TIMESTAMPTZ NOT NULL,
  usado BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE documentos_rag (
  id SERIAL PRIMARY KEY,
  fuente VARCHAR(150) NOT NULL,
  fragmento TEXT NOT NULL,
  embedding vector(768) NOT NULL
);
CREATE INDEX ix_rag_emb ON documentos_rag USING hnsw (embedding vector_cosine_ops);

CREATE TABLE consultas_bot (
  id BIGSERIAL PRIMARY KEY,
  usuario_id INT REFERENCES usuarios(id),
  pregunta TEXT NOT NULL,
  herramienta VARCHAR(80),
  creada_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 2.3 Decisiones de diseño

- El stock total de un medicamento no se guarda: se calcula con SUM sobre lotes. El stock real vive en lotes.cantidad\_actual y cada cambio deja un registro en movimientos (kárdex inmutable).
- El índice parcial ix\_lotes\_peps acelera la selección PEPS (el lote con caducidad más próxima y existencia).
- Las restricciones CHECK impiden stock negativo aunque falle la validación de la aplicación.
- La dimensión del vector (768) debe coincidir con el modelo de embeddings (nomic-embed-text usa 768).

## 3. Estructura del backend (FastAPI)

```
backend/
├── app/
│   ├── main.py                 # crea la app, CORS, routers
│   ├── core/
│   │   ├── config.py           # variables de entorno (pydantic-settings)
│   │   ├── database.py         # engine y sesión SQLAlchemy
│   │   ├── security.py         # JWT, hash de contraseñas
│   │   └── deps.py             # get_db, get_current_user, require_role
│   ├── models/                 # tablas SQLAlchemy
│   ├── schemas/                # modelos Pydantic (entrada y salida)
│   ├── repositories/           # consultas a la BD
│   ├── services/               # reglas de negocio
│   │   ├── auth_service.py
│   │   ├── inventory_service.py
│   │   ├── peps_service.py     # selección de lotes
│   │   ├── alert_service.py    # cálculo de alertas
│   │   └── report_service.py
│   ├── api/v1/routers/         # auth, usuarios, sucursales, medicamentos,
│   │                           # lotes, movimientos, alertas, reportes, telegram
│   ├── jobs/alerts_job.py      # APScheduler (CU-11)
│   └── ai/
│       ├── llm.py              # cliente Ollama
│       ├── tools.py            # herramientas LangChain que llaman a la API
│       ├── rag.py              # recuperación sobre pgvector
│       └── agent.py
├── bot/                        # proceso aparte (aiogram), solo habla con la API
├── alembic/                    # migraciones
├── tests/                      # pytest
└── requirements.txt
```

Capas: router (HTTP) → service (reglas) → repository (SQL). Esto da componentes con responsabilidades claras para el diagrama de componentes y para medir complejidad ciclomática por función.

## 4. Estructura del frontend (React + Vite)

```
frontend/src/
├── api/                # cliente axios con interceptor de token + funciones por recurso
├── app/                # router, layout, guards por rol
├── features/
│   ├── auth/           # login
│   ├── medicamentos/   # lista, formulario, escaneo
│   ├── inventario/     # existencias y lotes
│   ├── movimientos/    # entrada, salida, kárdex
│   ├── alertas/        # panel y configuración
│   ├── reportes/       # gráficas y exportación
│   ├── usuarios/       # usuarios y sucursales
│   └── telegram/       # vinculación
├── components/         # tablas, modales, inputs, badges de estado
├── hooks/              # useAuth, useBarcodeScanner
└── main.tsx
```

Librerías: React Router, TanStack Query (cache y estados de carga), React Hook Form + Zod (validación), Tailwind, Recharts (gráficas). El lector de código de barras se captura con un hook que detecta ráfagas rápidas de teclas terminadas en Enter.

## 5. Endpoints (prefijo /api/v1)

Roles: A = Administrador, E = Empleado (incluye A), Bot = token de servicio con el usuario vinculado.

| Método | Ruta | Rol | Función |
| --- | --- | --- | --- |
| POST | /auth/login | Público | Devuelve JWT |
| GET | /auth/me | A, E | Usuario actual |
| GET, POST | /usuarios | A | Listar, crear |
| PUT, PATCH | /usuarios/{id} | A | Editar, activar o desactivar |
| GET, POST, PUT | /sucursales | A | Gestión de sucursales |
| GET | /medicamentos?q=&page= | A, E | Listado y búsqueda |
| GET | /medicamentos/barcode/{codigo} | A, E | Búsqueda por código (CU-05) |
| POST, PUT | /medicamentos | A, E | Alta y modificación |
| DELETE | /medicamentos/{id} | A | Baja lógica |
| GET | /inventario?sucursal\_id=&q= | A, E | Existencias totales |
| GET | /medicamentos/{id}/lotes | A, E | Lotes de un medicamento |
| POST | /movimientos/entrada | A, E | Registrar entrada (CU-06) |
| POST | /movimientos/salida | A, E | Salida con PEPS (CU-07) |
| GET | /movimientos/peps-sugerido?medicamento\_id=&cantidad= | A, E | Lotes sugeridos sin confirmar |
| GET | /kardex?medicamento\_id=&lote\_id=&desde=&hasta= | A, E | Kárdex |
| GET | /alertas?tipo=&leida= | A, E | Panel de alertas |
| PATCH | /alertas/{id}/leida | A, E | Marcar como leída |
| GET, PUT | /alertas/configuracion | A | Días de anticipación |
| GET | /reportes/mermas?desde=&hasta= | A | Mermas por vencimiento |
| GET | /reportes/proximos-vencer?dias= | A | Próximos a vencer |
| GET | /reportes/inventario | A | Valuación de inventario |
| GET | /reportes/dashboard | A | Indicadores generales |
| POST | /telegram/codigo | A, E | Genera código de vinculación |
| POST | /telegram/vincular | Bot | Valida código y guarda chat\_id |
| POST | /bot/consulta | Bot | Entrada del agente LLM para el chat vinculado |

Las herramientas del LLM reutilizan los mismos endpoints de lectura: inventario, proximos-vencer, kardex y alertas. El LLM nunca accede a la BD.

Errores estándar: 400 validación de negocio, 401 sin sesión, 403 sin permiso, 404 no encontrado, 409 conflicto (código o lote duplicado), 422 validación Pydantic.

## 6. Consultas principales

**Existencias por medicamento (CU-08)**

```sql
SELECT m.id, m.nombre, m.codigo_barras, m.stock_minimo,
       COALESCE(SUM(l.cantidad_actual), 0) AS stock_total
FROM medicamentos m
LEFT JOIN lotes l ON l.medicamento_id = m.id
                 AND l.sucursal_id = :sucursal AND l.estado = 'ACTIVO'
WHERE m.activo AND (:q IS NULL OR lower(m.nombre) LIKE lower('%' || :q || '%'))
GROUP BY m.id
ORDER BY m.nombre;
```

**Selección PEPS con bloqueo para evitar ventas simultáneas (CU-07)**

```sql
SELECT id, numero_lote, fecha_caducidad, cantidad_actual
FROM lotes
WHERE medicamento_id = :med AND sucursal_id = :sucursal
  AND cantidad_actual > 0 AND fecha_caducidad >= CURRENT_DATE
ORDER BY fecha_caducidad ASC, id ASC
FOR UPDATE;
```

El servicio recorre los lotes en ese orden descontando hasta completar la cantidad, todo dentro de una sola transacción. Por cada lote afectado inserta un movimiento y actualiza cantidad\_actual.

**Productos próximos a vencer (CU-12 y reporte)**

```sql
SELECT l.id, m.nombre, l.numero_lote, l.fecha_caducidad,
       (l.fecha_caducidad - CURRENT_DATE) AS dias_restantes,
       l.cantidad_actual, l.cantidad_actual * l.costo_unitario AS valor_en_riesgo
FROM lotes l JOIN medicamentos m ON m.id = l.medicamento_id
WHERE l.sucursal_id = :sucursal AND l.cantidad_actual > 0
  AND l.fecha_caducidad BETWEEN CURRENT_DATE AND CURRENT_DATE + :dias
ORDER BY l.fecha_caducidad;
```

**Generación de alertas (CU-11), sin duplicar**

```sql
INSERT INTO alertas (lote_id, tipo, dias_umbral)
SELECT l.id, 'PROXIMO_VENCER', c.dias_anticipacion
FROM lotes l
JOIN configuracion_alertas c ON c.sucursal_id = l.sucursal_id
WHERE l.cantidad_actual > 0 AND l.estado = 'ACTIVO'
  AND l.fecha_caducidad >= CURRENT_DATE
  AND l.fecha_caducidad <= CURRENT_DATE + c.dias_anticipacion
ON CONFLICT (lote_id, tipo, dias_umbral) DO NOTHING;

UPDATE lotes SET estado = 'VENCIDO'
WHERE fecha_caducidad < CURRENT_DATE AND cantidad_actual > 0 AND estado = 'ACTIVO';
```

**Kárdex por producto (CU-09)**

```sql
SELECT mv.creado_en, l.numero_lote, mv.tipo, mv.cantidad, mv.saldo_lote,
       mv.costo_unitario, u.nombre AS usuario, mv.motivo
FROM movimientos mv
JOIN lotes l ON l.id = mv.lote_id
JOIN usuarios u ON u.id = mv.usuario_id
WHERE l.medicamento_id = :med
  AND (:lote IS NULL OR l.id = :lote)
  AND mv.creado_en BETWEEN :desde AND :hasta
ORDER BY mv.creado_en;
```

**Reporte de mermas por caducidad (CU-13)**

```sql
SELECT m.nombre, SUM(mv.cantidad) AS unidades_perdidas,
       SUM(mv.cantidad * mv.costo_unitario) AS perdida_economica
FROM movimientos mv
JOIN lotes l ON l.id = mv.lote_id
JOIN medicamentos m ON m.id = l.medicamento_id
WHERE mv.tipo = 'SALIDA_MERMA' AND l.sucursal_id = :sucursal
  AND mv.creado_en BETWEEN :desde AND :hasta
GROUP BY m.nombre
ORDER BY perdida_economica DESC;
```

La ordenación descendente por pérdida te sirve también como base para el análisis de Pareto del proyecto.

**Recuperación RAG (CU-16)**

```sql
SELECT fuente, fragmento
FROM documentos_rag
ORDER BY embedding <=> :embedding_pregunta
LIMIT 4;
```

## 7. Diagrama de componentes

&#91;embedded content: diagrama de componentes · 6 componentes propios, 2 externos\]

El bot nunca habla con la base de datos: solo llama a la API, y el módulo IA usa las mismas capas que la web. La recuperación del RAG consulta la tabla documentos\_rag de PostgreSQL.

| Componente | Responsabilidad | Tecnología |
| --- | --- | --- |
| Frontend | Interfaz web, escaneo y reportes | React, Vite, Tailwind |
| Routers API REST | Entrada HTTP, validación Pydantic, autenticación y roles | FastAPI, JWT |
| Servicios de negocio | PEPS, alertas, kárdex, reportes | Python |
| Repositorios | Acceso a datos | SQLAlchemy, Alembic |
| Tarea programada | Generación diaria de alertas | APScheduler |
| Módulo IA | Agente, herramientas y RAG | LangChain, Ollama |
| Bot de Telegram | Canal de consulta, solo cliente de la API | aiogram |

Componentes con lógica de decisión para el análisis de complejidad ciclomática, rutas de prueba, Pareto y valores límite: selección PEPS, generación de alertas, validación de salida de stock, validación de entrada de lote y autenticación con bloqueo por intentos.
