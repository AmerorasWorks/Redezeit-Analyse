import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import configparser


# 🔌 Verbindung zur PostgreSQL-Datenbank über .ini-Datei im Projekt-Hauptverzeichnis
def db_connect(config_file='../../config.ini', section='postgresql'):
    parser = configparser.ConfigParser()
    parser.read(config_file)

    if parser.has_section(section):
        db_params = {key: value for key, value in parser.items(section)}
    else:
        raise Exception(f"Sektion '{section}' nicht in '{config_file}' gefunden.")

    try:
        conn = psycopg2.connect(**db_params)
        print("✅ Verbindung zur Datenbank erfolgreich!")
        return conn
    except Exception as e:
        print("❌ Fehler bei der DB-Verbindung:", e)
        return None

# Verbindung aufbauen
conn = db_connect()

# Basis-Verbindung (ohne Datenbank)
base_conn_params = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "Datacraft",
}

# Ziel-Datenbank
TARGET_DB = "redezeit"