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
    "password": "Datacraft"
}

# Ziel-Datenbank
TARGET_DB = "redezeit"

# CSV-Quellen
CSV_FOLDER = r"C:\\Users\\Admin\\Desktop\\Redezeit-Analyse\\Data\\Scrapping data as csv"
CSV_TABLE_MAP = {
    "landingpage.csv": "landingpage",
    "user_behaviors.csv": "user_behaviors",
    "what_did_user_do.csv": "what_did_user_do",
    "where_did_they_come_from.csv": "where_did_they_come_from",
    "what_devices_used_chart.csv": "what_devices_used",
    "where_new_visitors_come_from_chart.csv": "where_new_visitors_come_from",
    "who_was_visiting_chart.csv": "who_was_visiting"
}

TABLES = list(CSV_TABLE_MAP.values())

def drop_and_create_database():
    conn = psycopg2.connect(**base_conn_params)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    cur.execute(f"""
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = '{TARGET_DB}' AND pid <> pg_backend_pid();
    """)

    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{TARGET_DB}'")
    if cur.fetchone():
        print(f"⚠️  Datenbank '{TARGET_DB}' existiert – wird gelöscht ...")
        cur.execute(f"DROP DATABASE {TARGET_DB}")
        print(f"🗑️  Datenbank '{TARGET_DB}' gelöscht.")

    cur.execute(f"CREATE DATABASE {TARGET_DB}")
    print(f"✅ Datenbank '{TARGET_DB}' wurde neu erstellt.")
    cur.close()
    conn.close()

def import_csv_to_postgres(csv_path, table_name, conn):
    df = pd.read_csv(csv_path, dayfirst=False)
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    if 'datum' in df.columns:
        df['datum'] = pd.to_datetime(df['datum'], errors='coerce').dt.date

    # NEU: Berechnung zeit_in_sekunden aus durchschn._zeit_auf_der_seite bei user_behaviors
    if table_name == "user_behaviors" and "durchschn._zeit_auf_der_seite" in df.columns:
        def parse_to_seconds(val):
            try:
                parts = str(val).split(":")
                parts = [int(p) for p in parts]
                if len(parts) == 2:  # mm:ss
                    return parts[0] * 60 + parts[1]
                elif len(parts) == 3:  # hh:mm:ss
                    return parts[0] * 3600 + parts[1] * 60 + parts[2]
            except:
                return None
        df["zeit_in_sekunden"] = df["durchschn._zeit_auf_der_seite"].apply(parse_to_seconds)

        # Spaltenreihenfolge anpassen: neue Spalte direkt nach 'durchschn._zeit_auf_der_seite'
        cols = list(df.columns)
        idx = cols.index("durchschn._zeit_auf_der_seite")
        cols.remove("zeit_in_sekunden")
        cols.insert(idx + 1, "zeit_in_sekunden")
        df = df[cols]

    def detect_type(series, col_name):
        if col_name == 'datum':
            return "DATE"
        try:
            as_int = pd.to_numeric(series.dropna(), downcast='integer')
            if (as_int == series.dropna()).all():
                return "INTEGER"
        except:
            pass
        try:
            pd.to_numeric(series.dropna(), errors='raise')
            return "FLOAT"
        except:
            pass
        return "TEXT"

    columns = df.columns
    col_types = {col: detect_type(df[col], col) for col in columns}

    with conn.cursor() as cur:
        col_defs = ", ".join([f'"{col}" {col_types[col]}' for col in columns])
        cur.execute(sql.SQL(f'''
            DROP TABLE IF EXISTS "{table_name}" CASCADE;
            CREATE TABLE "{table_name}" ({col_defs});
        '''))

        for _, row in df.iterrows():
            values = []
            for col in columns:
                val = row[col]
                if pd.isna(val):
                    values.append(None)
                else:
                    if col_types[col] == "INTEGER":
                        values.append(int(val))
                    elif col_types[col] == "FLOAT":
                        values.append(float(val))
                    else:
                        values.append(str(val))
            insert_query = sql.SQL(f'''
                INSERT INTO "{table_name}" ({', '.join(f'"{col}"' for col in columns)})
                VALUES ({', '.join(['%s'] * len(columns))})
            ''')
            cur.execute(insert_query, values)

        if 'datum' in df.columns and col_types['datum'] == 'DATE':
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

def fix_absprungrate(conn):
    with conn.cursor() as cur:
        cur.execute('''
            ALTER TABLE "user_behaviors" ADD COLUMN absprungrate_in_prozent FLOAT;
        ''')
        cur.execute('''
            UPDATE "user_behaviors"
            SET absprungrate_in_prozent = REPLACE(REPLACE(absprungrate, ',', '.'), '%', '')::FLOAT
            WHERE absprungrate IS NOT NULL;
        ''')
        cur.execute('''
            ALTER TABLE "user_behaviors" DROP COLUMN absprungrate;
        ''')
        conn.commit()
        print("✅ Spalte 'absprungrate' bereinigt → neue Spalte: 'absprungrate_in_prozent'")


def main():
    drop_and_create_database()
    conn = psycopg2.connect(**{**base_conn_params, "dbname": TARGET_DB})

    for csv_file, table in CSV_TABLE_MAP.items():
        path = os.path.join(CSV_FOLDER, csv_file)
        import_csv_to_postgres(path, table, conn)

    fix_absprungrate(conn)
    create_datum_index_and_constraints(conn)
    conn.close()

if __name__ == "__main__":
    main()