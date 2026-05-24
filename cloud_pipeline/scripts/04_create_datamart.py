import os

import psycopg2


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_FILE = os.path.join(BASE_DIR, "sql", "datamart.sql")

POSTGRES_USER = os.environ.get("POSTGRES_USER", "admin")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "admin123")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "retail_dw")


def main():
    """Ejecuta datamart.sql en PostgreSQL para crear o actualizar las vistas analíticas."""
    print("\n--- CREACIÓN DATAMART ---\n")

    with open(SQL_FILE) as f:
        sql = f.read()

    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=int(POSTGRES_PORT),
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
    conn.autocommit = True

    with conn.cursor() as cur:
        cur.execute(sql)

    conn.close()

    print("Datamart creado correctamente.")
    print("Vistas disponibles:")
    print("  - dm_ventas_por_categoria_mes")
    print("  - dm_ranking_shopping_mall")
    print("  - dm_evolucion_diaria")
    print("  - dm_dashboard_bi")


if __name__ == "__main__":
    main()
