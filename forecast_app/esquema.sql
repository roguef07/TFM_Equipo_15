CREATE TABLE IF NOT EXISTS datasets (
    id_dataset INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_dataset TEXT,
    tipo_origen TEXT,
    fecha_carga TEXT,
    hash_archivo TEXT,
    registros INTEGER,
    columnas TEXT
);

CREATE TABLE IF NOT EXISTS ventas (
    id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
    id_dataset INTEGER,
    fecha_venta TEXT NOT NULL,
    categoria TEXT NOT NULL,
    unidades_vendidas REAL NOT NULL,
    FOREIGN KEY(id_dataset) REFERENCES datasets(id_dataset)
);

CREATE TABLE IF NOT EXISTS modelos (
    id_modelo INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_modelo TEXT,
    version TEXT,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS ejecuciones (
    id_ejecucion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_dataset INTEGER,
    id_modelo INTEGER,
    parametros_json TEXT,
    horizonte INTEGER,
    fecha_ejecucion TEXT,
    metricas_json TEXT,
    estado TEXT,
    iteraciones INTEGER,
    FOREIGN KEY(id_dataset) REFERENCES datasets(id_dataset),
    FOREIGN KEY(id_modelo) REFERENCES modelos(id_modelo)
);

CREATE TABLE IF NOT EXISTS pronosticos (
    id_pronostico INTEGER PRIMARY KEY AUTOINCREMENT,
    id_ejecucion INTEGER,
    fecha_pronosticada TEXT,
    categoria TEXT,
    valor_pronosticado REAL,
    FOREIGN KEY(id_ejecucion) REFERENCES ejecuciones(id_ejecucion)
);