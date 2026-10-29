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