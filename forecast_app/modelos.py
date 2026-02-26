from datetime import datetime
from db import get_connection


def register_model(tipo, version="1.0", descripcion=""):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO modelos(
            tipo_modelo,
            version,
            descripcion,
            fecha_creacion
        )
        VALUES (?, ?, ?, ?)
    """, (
        tipo,
        version,
        descripcion,
        datetime.now().isoformat()
    ))

    id_modelo = cur.lastrowid
    conn.commit()
    conn.close()
    return id_modelo