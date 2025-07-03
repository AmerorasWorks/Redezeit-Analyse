import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2 import sql

# Base connection params (update your password, user, host, port if needed)
base_conn_params = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "Datacraft"
}

TARGET_DB = "redezeit"

TABLE_SCHEMAS = {
    "daily_visitors_chart": {
        "datum": "DATE",
        "kategorie": "TEXT",
        "wert": "INTEGER",
    },
    "device_usage": {
        "datum": "DATE",
        "kategorie": "TEXT",
        "wert": "FLOAT",
    },
    "landing_page_views": {
        "datum": "DATE",
        "eid": "FLOAT",
        "seitentitel": "TEXT",
        "aufrufe": "FLOAT",
    },
    "traffic_sources": {
        "datum": "DATE",
        "eid": "FLOAT",
        "quelle": "TEXT",
        "sitzungen": "INTEGER",
        "aufrufe": "FLOAT",
        "aufrufe_pro_sitzung": "FLOAT",
    },
    "traffic_source_chart": {
        "datum": "DATE",
        "kategorie": "TEXT",
        "wert": "INTEGER",
    },
    "user_events": {
        "datum": "DATE",
        "eid": "FLOAT",
        "name_des_events": "TEXT",
        "event_label": "TEXT",
        "aktive_nutzer": "INTEGER",
        "ereignisanzahl": "INTEGER",
    },
    "user_sessions": {
        "datum": "DATE",
        "seitenaufrufe": "FLOAT",
        "nutzer_insgesamt": "INTEGER",
        "durchschn_zeit_auf_der_seite": "TEXT",
        "absprungrate": "FLOAT",
        "seiten_sitzung": "FLOAT",
        "durchschn_zeit_auf_der_seite_seconds": "FLOAT",
        "durchschn_zeit_auf_der_seite_days": "FLOAT",
    }
}




def drop_and_create_database():
    """
    Drops and recreates the TARGET_DB database.

    Args:
        None

    Returns:
        None

    Raises:
        psycopg2.Error: If connection or SQL execution fails.
    """
    conn = psycopg2.connect(**base_conn_params)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Terminate other connections to the target DB
    cur.execute("""
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = %s AND pid <> pg_backend_pid();
    """, (TARGET_DB,))

    # Drop DB if exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TARGET_DB,))
    if cur.fetchone():
        print(f"⚠️ Database '{TARGET_DB}' exists — dropping it...")
        cur.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(TARGET_DB)))
        print(f"🗑️ Database '{TARGET_DB}' dropped.")

    # Create new DB
    cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(TARGET_DB)))
    print(f"✅ Database '{TARGET_DB}' created.")

    cur.close()
    conn.close()


def create_tables():
    """
    Creates all tables in TARGET_DB based on TABLE_SCHEMAS.

    Args:
        None

    Returns:
        None

    Raises:
        psycopg2.Error: If connection or SQL execution fails.
    """
    conn = psycopg2.connect(**{**base_conn_params, "dbname": TARGET_DB})
    cur = conn.cursor()

    for table_name, columns in TABLE_SCHEMAS.items():
        col_defs = ", ".join([f'"{col}" {dtype}' for col, dtype in columns.items()])
        drop_create_query = sql.SQL("""
            DROP TABLE IF EXISTS {table} CASCADE;
            CREATE TABLE {table} ({cols});
        """).format(
            table=sql.Identifier(table_name),
            cols=sql.SQL(col_defs)
        )
        cur.execute(drop_create_query)
        print(f"✅ Table '{table_name}' created.")

        if "Datum" in columns:
            index_query = sql.SQL("""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON {table} ("Datum");
            """).format(
                index_name=sql.Identifier(f"idx_{table_name}_datum"),
                table=sql.Identifier(table_name)
            )
            cur.execute(index_query)
            print(f"🔖 Index created on '{table_name}.Datum'")

    conn.commit()
    cur.close()
    conn.close()


def main():
    """
    Main execution function to drop, recreate the database and tables.

    Args:
        None

    Returns:
        None
    """
    drop_and_create_database()
    create_tables()
    print("🎉 Schema creation complete.")


if __name__ == "__main__":
    main()
