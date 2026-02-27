import pandas as pd
import hashlib
from datetime import datetime
from db import get_connection


def hash_file(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()


def ingest_csv(file, filename):
    df = pd.read_csv(file)

    # Validación de columnas obligatorias
    required_cols = {"fecha_venta", "categoria", "unidades_vendidas"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"El CSV debe contener las columnas: {required_cols}")

    file_bytes = file.getvalue()
    file_hash = hash_file(file_bytes)

    conn = get_connection()
    cur = conn.cursor()

    # --- guardar metadata dataset ---
    cur.execute("""
        INSERT INTO datasets(
            nombre_dataset,
            tipo_origen,
            fecha_carga,
            hash_archivo,
            n_registros,
            columnas
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        filename,
        "csv",
        datetime.now().isoformat(),
        file_hash,
        len(df),
        ",".join(df.columns)
    ))

    id_dataset = cur.lastrowid

    # --- preparar datos en memoria (batch insert) ---
    rows = []
    for _, row in df.iterrows():
        rows.append((
            id_dataset,
            str(row["fecha_venta"]),
            str(row["categoria"]),
            float(row["unidades_vendidas"])
        ))

    # --- inserción por lotes (MUCHO más rápido) ---
    cur.executemany("""
        INSERT INTO ventas(
            id_dataset,
            fecha_venta,
            categoria,
            unidades_vendidas
        )
        VALUES (?, ?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()

    return id_dataset