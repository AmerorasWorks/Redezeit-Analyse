import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path

# --- CONFIGURATION SECTION ---

# Name of the PostgreSQL database
DATABASE_NAME = "redezeit"

# Folder path to cleaned CSV files
DATA_FOLDER = Path("src/data/clean")

# Schema definitions: expected column names (lowercase) and data types for each table
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


# ---Cleaning and casting function---

# Clean and cast columns to correct types, based on content patterns
def clean_and_cast_columns(df):
    errors = {}  # track columns where conversion failed

    for col in df.columns:
        is_obj = df[col].dtype == "object"
        sample = df[col].dropna().astype(str) if is_obj else None

        # --- Handle date columns ---
        if "datum" in col.lower():
            converted = pd.to_datetime(df[col], errors="coerce")
            failed = converted.isna() & df[col].notna()
            if failed.any():
                errors[col] = {'datetime_failures': failed.sum()}
            df[col] = converted
            continue

        # --- Handle HH:MM:SS time duration columns ---
        if is_obj and sample.str.match(r"^\d{2}:\d{2}:\d{2}$").all():
            td = pd.to_timedelta(df[col], errors="coerce")
            failed = td.isna() & df[col].notna()
            if failed.any():
                errors[col] = {'timedelta_failures': failed.sum()}
            df[col] = td.astype(str).str[-8:]  # keep "HH:MM:SS"
            df[f"{col}_seconds"] = td.dt.total_seconds()  # add duration in seconds
            df[f"{col}_days"] = td.dt.total_seconds() / 86400  # duration in days
            continue

        # --- Handle percentage columns like "12.5%" ---
        if is_obj and sample.str.match(r"^[\d\.\,]+\s*%$").all():
            stripped = sample.str.replace("%", "", regex=False).str.replace(",", ".", regex=False)
            converted = pd.to_numeric(stripped, errors="coerce") / 100
            failed = converted.isna() & df[col].notna()
            if failed.any():
                errors[col] = {'percentage_failures': failed.sum()}
            df[col] = converted
            continue

        # --- Handle numeric data already in float/int format ---
        if not is_obj:
            if pd.api.types.is_integer_dtype(df[col]):
                continue
            elif pd.api.types.is_float_dtype(df[col]):
                if (df[col].dropna() % 1 == 0).all():
                    df[col] = df[col].astype('Int64')  # cast float to integer if safe
                continue
            else:
                df[col] = df[col].astype(float)
                continue

        # --- Handle numeric strings like "123", "45.6" ---
        if is_obj:
            if sample.str.match(r"^\d+(\.\d+)?$").all():
                converted = pd.to_numeric(df[col], errors="coerce")
                failed = converted.isna() & df[col].notna()
                if failed.any():
                    errors[col] = {'numeric_failures': failed.sum()}
                    df[col] = df[col].astype(str)
                else:
                    if (converted.dropna() % 1 == 0).all():
                        df[col] = converted.astype('Int64')
                    else:
                        df[col] = converted.astype(float)
                continue

            # --- Default: keep text columns as string ---
            df[col] = sample

    if errors:
        print(f"⚠️ Casting errors found: {errors}")
    else:
        print("✅ All columns cleaned and cast successfully.")
    return df


# --- FUNCTION TO POPULATE TABLES FROM CSV ---

def populate_table_from_csv(conn, table_name, csv_path):
    print(f"\n📥 Loading {csv_path.name} into '{table_name}'...")

    # 1) Read CSV into DataFrame
    df = pd.read_csv(csv_path, delimiter=';')

    # 2) Normalize headers
    df.columns = df.columns.str.strip().str.lower()

    # 3) Clean & cast your columns
    df = clean_and_cast_columns(df)

    # 4) Select only the schema‑defined columns
    expected_cols = list(TABLE_SCHEMAS[table_name].keys())
    df = df[expected_cols]

    # 5) Replace ALL pandas NAs/NaNs/NaTs with Python None
    df = df.where(pd.notnull(df), None)

    # 5.5) Replace pandas.NA with None explicitly
    df = df.map(lambda x: None if x is pd.NA else x)

    # 6) Force pure‑Python object dtype (so pandas won't re‑wrap your None)
    df = df.astype(object)

    # 7) Build the quoted‑columns INSERT template
    cols_quoted = ', '.join(f'"{c}"' for c in expected_cols)
    query      = f"INSERT INTO {table_name} ({cols_quoted}) VALUES %s"

    # 8) Turn each row into a Python tuple (None stays None)
    rows = list(df.itertuples(index=False, name=None))

    # 9) Bulk insert
    with conn.cursor() as cur:
        try:
            execute_values(cur, query, rows)
            conn.commit()
            print(f"✅ Inserted {len(rows)} rows into '{table_name}'")
        except Exception as e:
            conn.rollback()
            print(f"❌ Failed inserting into '{table_name}': {e}")




# --- MAIN EXECUTION SECTION ---

def main():
    # Connect to the local PostgreSQL database
    conn = psycopg2.connect(
        dbname="redezeit",
        user="postgres",
        password="Datacraft",
        host="localhost",
        
    )

    # Loop through all defined tables and process their matching CSV files
    for table_name, schema in TABLE_SCHEMAS.items():
        csv_file = DATA_FOLDER / f"{table_name}.csv"
        if csv_file.exists():
            populate_table_from_csv(conn, table_name, csv_file)
        else:
            print(f"⚠️ Missing file: {csv_file.name}")

    # Close connection when done
    conn.close()
    print("\n✅ All tables processed.")

# Standard Python entry point
if __name__ == "__main__":
    main()
