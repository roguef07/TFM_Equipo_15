import json
from datetime import datetime
from db import get_connection

def create_execution(id_dataset, id_modelo, horizonte, params):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO ejecuciones(
            id_dataset, 
            id_modelo, 
            parametros_json,
            horizonte,
            fecha_ejecucion, 
            estado
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        id_dataset,
        id_modelo,
        json.dumps(params),
        horizonte,
        datetime.now().isoformat(),
        "RUNNING"
    ))

    id_ejecucion = cur.lastrowid
    conn.commit()
    conn.close()
    return id_ejecucion


