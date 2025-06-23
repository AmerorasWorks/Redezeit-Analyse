import os
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Basis-Verbindung (ohne Datenbank)
base_conn_params = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "Datacraft"  # ← bitte anpassen
}

# Ziel-Datenbank
TARGET_DB = "redezeit"

# CSV-Quellen
CSV_FOLDER = r"C:\Users\Admin\Desktop\Redezeit-Analyse\Data\Scrapping data as csv"  # ← ggf. Pfad anpassen
CSV_TABLE_MAP = {
    "landingpage.csv": "landingpage",
    "user_behaviors.csv": "user_behaviors",
    "what_did_user_do.csv": "what_did_user_do",
    "where_did_they_come_from.csv": "where_did_they_come_from",
    "what_devices_used_chart.csv": "what_devices_used",
    "where_new_visitors_come_from_chart.csv": "where_new_visitors_come_from",
    "who_was_visiting_chart.csv": "who_was_visiting"
}

# Liste aller Tabellennamen
TABLES = list(CSV_TABLE_MAP.values())

def drop_and_create_database():
    conn = psycopg2.connect(**base_conn_params)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Verbindungen zur Ziel-Datenbank schließen
    cur.execute(f"""
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = '{TARGET_DB}' AND pid <> pg_backend_pid();
    """)

    # Löschen, falls existiert
    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{TARGET_DB}'")
    if cur.fetchone():
        print(f"⚠️  Datenbank '{TARGET_DB}' existiert – wird gelöscht ...")
        cur.execute(f"DROP DATABASE {TARGET_DB}")
        print(f"🗑️  Datenbank '{TARGET_DB}' gelöscht.")

    # Neu erstellen
    cur.execute(f"CREATE DATABASE {TARGET_DB}")
    print(f"✅ Datenbank '{TARGET_DB}' wurde neu erstellt.")
    cur.close()
    conn.close()


def import_csv_to_postgres(csv_path, table_name, conn):
    df = pd.read_csv(csv_path, dayfirst=False, parse_dates=["Datum"])  # still parse, aber sauber
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    if 'datum' in df.columns:
        df['datum'] = pd.to_datetime(df['datum'], errors='coerce').dt.date

    with conn.cursor() as cur:
        columns = df.columns
        col_defs = ", ".join([
            f'"{col}" DATE' if col == 'datum' else f'"{col}" TEXT'
            for col in columns
        ])

        cur.execute(sql.SQL(f'''
            DROP TABLE IF EXISTS "{table_name}" CASCADE;
            CREATE TABLE "{table_name}" ({col_defs});
        '''))

        for _, row in df.iterrows():
            values = [row[col] for col in columns]
            insert_query = sql.SQL(f'''
                INSERT INTO "{table_name}" ({', '.join(f'"{col}"' for col in columns)})
                VALUES ({', '.join(['%s'] * len(columns))})
            ''')
            cur.execute(insert_query, values)

        # Index auf datum
        if 'datum' in df.columns:
            cur.execute(sql.SQL(f'''
                CREATE INDEX IF NOT EXISTS idx_{table_name}_datum ON "{table_name}" (datum)
            '''))

        conn.commit()
        print(f"✅ Tabelle '{table_name}' importiert & indexiert.")

def create_datum_index_and_constraints(conn):
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS datum_index CASCADE;")
        cur.execute('''
            CREATE TABLE datum_index (
                datum DATE PRIMARY KEY
            )
        ''')

        for table in TABLES:
            cur.execute(sql.SQL(f'''
                INSERT INTO datum_index (datum)
                SELECT DISTINCT datum FROM "{table}"
                WHERE datum IS NOT NULL
                ON CONFLICT (datum) DO NOTHING;
            '''))

        for table in TABLES:
            cur.execute(sql.SQL(f'''
                ALTER TABLE "{table}"
                ADD CONSTRAINT fk_{table}_datum
                FOREIGN KEY (datum)
                REFERENCES datum_index (datum)
            '''))

        conn.commit()
        print("✅ Fremdschlüssel & zentrale datum_index erstellt.")

def main():
    drop_and_create_database()
    conn = psycopg2.connect(**{**base_conn_params, "dbname": TARGET_DB})

    for csv_file, table in CSV_TABLE_MAP.items():
        path = os.path.join(CSV_FOLDER, csv_file)
        import_csv_to_postgres(path, table, conn)

    create_datum_index_and_constraints(conn)
    conn.close()

if __name__ == "__main__":
    main()
