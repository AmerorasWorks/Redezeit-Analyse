import os
import pandas as pd
import psycopg2
from psycopg2 import sql
import configparser

# ─────────────────────────────────────────────────────────────
#  Supabase conn params
# ─────────────────────────────────────────────────────────────
def load_db_config(config_file, section):
    parser = configparser.ConfigParser()
    parser.read(config_file)

    if not parser.has_section(section):
        raise Exception(f"Sektion '{section}' nicht in '{config_file}' gefunden.")

    config = {key: value for key, value in parser.items(section)}

    if config.get("enabled", "false").lower() != "true":
        print(f"ℹ️ Verbindung für '{section}' ist in der Konfiguration deaktiviert.")
        return None

    # Port muss int sein für psycopg2
    config["port"] = int(config["port"])
    return config


#  Target schema in Supabase (instead of creating a new DB)
TARGET_SCHEMA = "redezeit"

#  Where to find the CSV files
CSV_FOLDER = os.path.join(os.path.dirname(__file__), "..", "data", "clean")
CSV_FOLDER = os.path.abspath(CSV_FOLDER)

#  CSV to table mapping
CSV_TABLE_MAP = {
    "landing_page_views.csv": "landing_page_views",
    "user_sessions.csv": "user_sessions",
    "device_usage.csv": "device_usage",
    "user_events.csv": "user_events",
    "traffic_sources.csv": "traffic_sources",
    "traffic_source_chart.csv": "traffic_source_chart",
    "daily_visitors_chart.csv": "daily_visitors_chart",
}

TABLES = list(CSV_TABLE_MAP.values())

# ─────────────────────────────────────────────────────────────
#  Utility to ensure the target schema exists
# ─────────────────────────────────────────────────────────────
def ensure_schema_exists(conn):
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL(f"CREATE SCHEMA IF NOT EXISTS {TARGET_SCHEMA};")
        )
        # Set the default schema path for this session
        cur.execute(
            sql.SQL(f"SET search_path TO {TARGET_SCHEMA};")
        )
    print(f"✅ Schema '{TARGET_SCHEMA}' exists and is active.")

# ─────────────────────────────────────────────────────────────
#  CSV to PostgreSQL importer
# ─────────────────────────────────────────────────────────────
def import_csv_to_postgres(csv_path, table_name, conn):
    print(f"📄 Lade CSV: {csv_path}")
    df = pd.read_csv(csv_path, sep=";", dayfirst=False)
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    # Normalize date column if present
    if "datum" in df.columns:
        df["datum"] = pd.to_datetime(df["datum"], errors="coerce").dt.date

    # Special logic for session times
    if table_name == "user_sessions" and "durchschn._zeit_auf_der_seite" in df.columns:
        def parse_to_seconds(val):
            try:
                parts = str(val).split(":")
                parts = [int(p) for p in parts]
                if len(parts) == 2:
                    return parts[0] * 60 + parts[1]
                elif len(parts) == 3:
                    return parts[0] * 3600 + parts[1] * 60 + parts[2]
            except:
                return None

        df["zeit_in_sekunden"] = df["durchschn._zeit_auf_der_seite"].apply(parse_to_seconds)

        # Reorder columns so the new one is right after the original
        cols = list(df.columns)
        idx = cols.index("durchschn._zeit_auf_der_seite")
        cols.remove("zeit_in_sekunden")
        cols.insert(idx + 1, "zeit_in_sekunden")
        df = df[cols]

    # Infer SQL types based on Pandas dtype
    def detect_type(series, col_name):
        if col_name == "datum":
            return "DATE"
        try:
            as_int = pd.to_numeric(series.dropna(), downcast="integer")
            if (as_int == series.dropna()).all():
                return "INTEGER"
        except:
            pass
        try:
            pd.to_numeric(series.dropna(), errors="raise")
            return "FLOAT"
        except:
            pass
        return "TEXT"

    columns = df.columns
    col_types = {col: detect_type(df[col], col) for col in columns}

    with conn.cursor() as cur:
        # Set search_path again to be safe
        cur.execute(sql.SQL(f"SET search_path TO {TARGET_SCHEMA};"))

        # Drop and recreate table
        col_defs = ", ".join([f'"{col}" {col_types[col]}' for col in columns])
        cur.execute(
            sql.SQL(
                f"""
                DROP TABLE IF EXISTS "{table_name}" CASCADE;
                CREATE TABLE "{table_name}" ({col_defs});
            """
            )
        )

        # Insert rows
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
            insert_query = sql.SQL(
                f"""
                INSERT INTO "{table_name}" ({', '.join(f'"{col}"' for col in columns)})
                VALUES ({', '.join(['%s'] * len(columns))});
                """
            )
            cur.execute(insert_query, values)

        # Optional: Index on datum
        if "datum" in df.columns and col_types["datum"] == "DATE":
            cur.execute(
                sql.SQL(
                    f"""
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_datum ON "{table_name}" (datum);
                    """
                )
            )

        conn.commit()
        print(f"✅ Tabelle '{table_name}' importiert & indexiert.")

# ─────────────────────────────────────────────────────────────
#  Fix percent column (if needed)
# ─────────────────────────────────────────────────────────────
def fix_absprungrate(conn):
    with conn.cursor() as cur:
        cur.execute(sql.SQL(f"SET search_path TO {TARGET_SCHEMA};"))
        cur.execute(
            """
            ALTER TABLE "user_sessions" ADD COLUMN absprungrate_in_prozent FLOAT;
            """
        )
        cur.execute(
            """
            UPDATE "user_sessions"
            SET absprungrate_in_prozent = REPLACE(absprungrate, '%', '')::FLOAT
            WHERE absprungrate IS NOT NULL;
            """
        )
        cur.execute(
            """
            ALTER TABLE "user_sessions" DROP COLUMN absprungrate;
            """
        )
        conn.commit()
        print("✅ Spalte 'absprungrate' bereinigt.")

# ─────────────────────────────────────────────────────────────
#  Datum-Index Tabelle & Constraints
# ─────────────────────────────────────────────────────────────
def create_datum_index_and_constraints(conn):
    with conn.cursor() as cur:
        cur.execute(sql.SQL(f"SET search_path TO {TARGET_SCHEMA};"))

        cur.execute("DROP TABLE IF EXISTS datum_index CASCADE;")
        cur.execute(
            """
            CREATE TABLE datum_index (
                datum DATE PRIMARY KEY
            );
            """
        )

        for table in TABLES:
            cur.execute(
                sql.SQL(
                    f"""
                    INSERT INTO datum_index (datum)
                    SELECT DISTINCT datum FROM "{table}"
                    WHERE datum IS NOT NULL
                    ON CONFLICT (datum) DO NOTHING;
                    """
                )
            )

        for table in TABLES:
            cur.execute(
                sql.SQL(
                    f"""
                    ALTER TABLE "{table}"
                    ADD CONSTRAINT fk_{table}_datum
                    FOREIGN KEY (datum)
                    REFERENCES datum_index (datum);
                    """
                )
            )

        conn.commit()
        print("✅ Fremdschlüssel & zentrale datum_index erstellt.")


# ─────────────────────────────────────────────────────────────
# 🕓 Tabelle für letzte Aktualisierung
# ─────────────────────────────────────────────────────────────
def update_last_updated_table(conn):
    with conn.cursor() as cur:
        cur.execute(sql.SQL(f"SET search_path TO {TARGET_SCHEMA};"))

        # Create table if it doesn't exist
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS last_updated (
                table_name TEXT PRIMARY KEY,
                updated_at TIMESTAMP
            );
            """
        )

        # Insert/update for each table
        from datetime import datetime
        for table in TABLES:
            cur.execute(
                sql.SQL(
                    """
                    INSERT INTO last_updated (table_name, updated_at)
                    VALUES (%s, %s)
                    ON CONFLICT (table_name) DO UPDATE
                    SET updated_at = EXCLUDED.updated_at;
                    """
                ),
                [table, datetime.utcnow()]
            )

        # Global update marker
        cur.execute(
            """
            INSERT INTO last_updated (table_name, updated_at)
            VALUES ('__ALL__', %s)
            ON CONFLICT (table_name) DO UPDATE
            SET updated_at = EXCLUDED.updated_at;
            """,
            [datetime.utcnow()]
        )

        conn.commit()
        print("✅ Tabelle 'last_updated' aktualisiert.")

# ─────────────────────────────────────────────────────────────
# 🚀 Main Execution Flow
# ─────────────────────────────────────────────────────────────
def main():
    print("🔗 Verbinde mit Supabase ...")
    CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config.ini'))
    supabase_conn_params = load_db_config(CONFIG_PATH, 'supabase')

    if supabase_conn_params is None:
        print("❌ Verbindung abgebrochen – Supabase-Konfiguration deaktiviert oder fehlerhaft.")
        return

    conn = psycopg2.connect(**supabase_conn_params)


    ensure_schema_exists(conn)

    for csv_file, table in CSV_TABLE_MAP.items():
        path = os.path.join(CSV_FOLDER, csv_file)
        if not os.path.isfile(path):
            print(f"❌ CSV nicht gefunden: {path}")
            continue
        import_csv_to_postgres(path, table, conn)

    fix_absprungrate(conn)
    create_datum_index_and_constraints(conn)

    # 🔄 Add timestamp to 'last_updated' table
    update_last_updated_table(conn)

    conn.close()
    print("🏁 Fertig.")

# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
