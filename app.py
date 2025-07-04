import streamlit as st
from datetime import date, timedelta
import pickle
import os
import sys
from pathlib import Path
import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service


def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def load_custom_css(relative_css_path: str):
    css_file = resource_path(relative_css_path)
    if not os.path.isfile(css_file):
        st.error(f"CSS nicht gefunden: {css_file}")
        return
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Log-Datei für bereits gescrapte Daten
SCRAPE_LOG_PATH = os.path.join("src", "data", "log", "scrape_log.csv")

# Lokale Tools (du musst sicherstellen, dass diese Module im selben Ordner liegen oder per sys.path importierbar sind)
sys.path.append(os.path.dirname(__file__))

from src.utils.kalender_funktion import select_date_range
from src.utils.csv_manager import CSVFileHandler
from src.utils.cleaning_csv import prepare_data_paths, copy_and_validate_csvs

# Importiere alle Scraper-Funktionen
from src.scraper.landingpage_scraper import (
    extract_table_data as extract_landingpage_data,
)
from src.scraper.user_behaviors_scraper import extract_user_behaviour
from src.scraper.what_did_users_do_scraper import (
    extract_table_data as extract_events_data,
)
from src.scraper.where_did_they_come_from_scraper import (
    extract_table_data as extract_sources_data,
)
from src.scraper.where_new_visitors_come_from_chart import (
    extract_table_for_piechart_gviz as extract_pie_sources,
)
from src.scraper.what_devices_used_chart import (
    extract_table_for_piechart_gviz as extract_pie_devices,
)
from src.scraper.who_was_visiting_chart import (
    extract_table_for_piechart_gviz as extract_pie_visitors,
)


def get_chrome_driver() -> webdriver.Chrome:
    """
    Erzeugt einen Chrome-Webdriver, der immer den mit PyInstaller gebündelten
    chromedriver.exe verwendet.
    """
    chrome_path = resource_path("chromedriver.exe")
    service     = Service(executable_path=chrome_path)
    options     = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    return webdriver.Chrome(service=service, options=options)


def ensure_cookie_dir(folder_name: str = "cookies") -> Path:
    """
    Ermittelt ein beschreibbares Basis-Verzeichnis neben der EXE (One-File)
    oder im Projektordner (Dev-Mode) und legt darin einen Unterordner
    mit dem Namen `folder_name` an, falls er noch nicht existiert.

    :param folder_name: Name des Unterordners, standardmäßig "cookies"
    :return: Path-Objekt zum angelegten Verzeichnis
    """
    # Basis-Verzeichnis wählen
    if getattr(sys, "frozen", False):
        # im gebündelten One-File-Modus ist sys.executable die EXE
        base_dir = Path(sys.executable).parent
    else:
        # im Skript-Modus das Verzeichnis der aktuellen Datei
        base_dir = Path(__file__).parent

    # Unterordner anlegen, falls nicht vorhanden
    cookie_dir = base_dir / folder_name
    cookie_dir.mkdir(exist_ok=True)

    return cookie_dir

COOKIE_DIR = ensure_cookie_dir()
COOKIE_PATH = COOKIE_DIR / "cookies.pkl"
URL = "https://lookerstudio.google.com/u/0/reporting/3c1fa903-4f31-4e6f-9b54-f4c6597ffb74/page/4okDC"


def is_date_scraped(scrape_date: date) -> bool:
    """
    Prüft, ob 'scrape_date' bereits in SCRAPE_LOG_PATH geloggt wurde.
    Verhindert Doppel-Scrapes – niemand mag Repeat-Dates! 😄
    """
    if not os.path.exists(SCRAPE_LOG_PATH):
        return False

    with open(SCRAPE_LOG_PATH, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # Header überspringen
        for row in reader:
            if row and row[0] == scrape_date.isoformat():
                return True
    return False


def log_scraped_date(scrape_date: date) -> None:
    """
    Loggt 'scrape_date' ans Ende von SCRAPE_LOG_PATH.
    Legt Ordner und Datei bei Bedarf an – Out-of-the-box ready!
    """
    os.makedirs(os.path.dirname(SCRAPE_LOG_PATH), exist_ok=True)
    file_exists = os.path.exists(SCRAPE_LOG_PATH)

    with open(SCRAPE_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Datum"])  # Header anlegen
        writer.writerow([scrape_date.isoformat()])


if "log_messages" not in st.session_state:
    st.session_state.log_messages = []


def log(message: str, level: str = "info") -> None:
    from datetime import datetime

    colors = {
        "info": "#000000",
        "warning": "#7b4b02",
        "error": "#600a0a",
        "success": "#000000",
    }
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    color = colors.get(level, "#000000")
    styled_message = f'<div style="color: {color}; font-family: monospace;">[{timestamp}] {message}</div>'
    st.session_state.log_messages.append(styled_message)


def show_log(container):
    container.markdown(
        f"""
        <div id="log-container">
        {"".join(st.session_state.log_messages)}
        </div>
        """,
        unsafe_allow_html=True,
    )





# === Initialisiere Chrome mit gespeicherten CookiesCookies ===
def init_driver_with_cookies():
    driver = get_chrome_driver()
    driver.get(URL)

    if COOKIE_PATH.exists():
        with open(COOKIE_PATH, "rb") as f:
            cookies = pickle.load(f)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                pass
        driver.refresh()
        time.sleep(5)
    else:
        st.warning("🔐 Bitte anmelden und dann erneut klicken.")
        st.stop()

    return driver


# === Cookies speichern ===
def save_cookies(driver):
    # schreibt jetzt in den beschreibbaren Ordner neben der EXE
    with open(COOKIE_PATH, "wb") as f:
        pickle.dump(driver.get_cookies(), f)


# === Alle Scraper ausführen ===
def run_all_scraper(start_date, end_date, log_container=None):
    # beschreibbaren Output-Ordner neben der EXE anlegen
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).parent

    output_folder = base_dir / "data" / "raw"
    output_folder.mkdir(parents=True, exist_ok=True)

    driver = init_driver_with_cookies()

    current = start_date
    while current <= end_date:
        if is_date_scraped(current):
            log(f"📅 {current.isoformat()} schon gescrapt – überspringe.", "info")
            if log_container:
                show_log(log_container)
            current += timedelta(days=1)
            continue

        log(f"\n📆 Scraping für {current.isoformat()}", "info")
        if log_container:
            show_log(log_container)
        try:
            select_date_range(driver, current, current)
            time.sleep(8)

            data = extract_landingpage_data(driver, current.isoformat())
            lp_csv = CSVFileHandler(
                os.path.join(output_folder, f"landingpage.csv"),
                headers=[
                    "datum", 
                    "eid", 
                    "seitentitel", 
                    "aufrufe"
                ],
            )
            for row in data:
                lp_csv.append_row(row)

            row = extract_user_behaviour(driver, current)
            if row:
                ub_csv = CSVFileHandler(
                    os.path.join(output_folder, f"user_behaviors.csv"),
                    headers=[
                        "datum",
                        "seitenaufrufe",
                        "nutzer insgesamt",
                        "durchschn. zeit auf der seite",
                        "absprungrate",
                        "seiten / sitzung",
                    ],
                )
                ub_csv.append_row(row)

            data = extract_events_data(driver, current.isoformat())
            ev_csv = CSVFileHandler(
                os.path.join(output_folder, f"what_did_user_do.csv"),
                headers=[
                    "datum",
                    "eid",
                    "name des events",
                    "event_label",
                    "aktive nutzer",
                    "ereignisanzahl",
                ],
            )
            for row in data:
                ev_csv.append_row(row)

            data = extract_sources_data(driver, current.isoformat())
            src_csv = CSVFileHandler(
                os.path.join(output_folder, f"where_did_they_come_from.csv"),
                headers=[
                    "datum",
                    "eid",
                    "quelle",
                    "sitzungen",
                    "aufrufe",
                    "aufrufe pro sitzung",
                ],
            )
            for row in data:
                src_csv.append_row(row)

            for label, func in zip(
                [
                    "where_new_visitors_come_from_chart",
                    "what_devices_used_chart",
                    "who_was_visiting_chart",
                ],
                [extract_pie_sources, extract_pie_devices, extract_pie_visitors],
            ):
                pie_data = func(driver, current.isoformat())
                pie_csv = CSVFileHandler(
                    os.path.join(output_folder, f"{label}.csv"),
                    headers=["datum", "kategorie", "wert"],
                )
                for row in pie_data:
                    pie_csv.append_row(row)

        except Exception as e:
            log(f"❌ Fehler am {current}: {e}", "error")
            if log_container:
                show_log(log_container)
        else:
            log_scraped_date(current)
            log(f"✅ {current.isoformat()} geloggt.", "success")
            if log_container:
                show_log(log_container)
        finally:
            current += timedelta(days=1)

    driver.quit()  # Wichtig: erst WebDriver schließen
    time.sleep(5)  # Mini-Wartezeit zum Dateischreiben

    paths = prepare_data_paths()
    raw_files_exist = any(
        os.path.exists(os.path.join(paths["output_folder"], fname))
        for fname in paths["file_names"]
    )
    if raw_files_exist:
        copy_and_validate_csvs(paths, log=log, show_log=show_log, log_container=log_container)
        log("✅ Alle CSV-Dateien wurden erfolgreich aufbereitet.", "success")
    else:
        log(
            "⚠️ Keine Rohdaten gefunden – möglicherweise ist beim Scraping etwas schiefgelaufen.",
            "warning",
        )

    if log_container:
        show_log(log_container)


# Log-Fenster-Funktion angepasst, kein inline style mehr
def show_log(container):
    container.markdown(
        f"""
        <div id="log-container">
        {"".join(st.session_state.log_messages)}
        </div>
        """,
        unsafe_allow_html=True,
    )


# Load CSS file
load_custom_css("style.css")


# === Streamlit UI ===
def main():
    # === CSS hier ganz oben laden ===
    load_custom_css("style.css")

    st.markdown(
        """
    <style>
        header {visibility: hidden;}
    </style>

    <div class="custom-header">
        <div class="title"><h1>scrapetime</h1></div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("<hr style='border:1px solid #004709;'>", unsafe_allow_html=True)

    st.subheader("Willkommen zum Redezeit-Scraping-Tool!")
    st.markdown(
        """
        <div class="custom-info">
            Hier kannst du Daten vom Redezeit-Dashboard extrahieren und in CSV-Dateien speichern.<br>
            Bitte beachte, dass du dich einmalig bei Google anmelden musst, um die Cookies zu speichern.<br>
            Danach kannst du die Scraper für einen bestimmten Zeitraum ausführen.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<hr style='border:1px solid #004709;'>", unsafe_allow_html=True)

    with st.container():
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            start_date = st.date_input(
                "Startdatum", date.today() - timedelta(days=7), key="start"
            )
            end_date = st.date_input(
                "Enddatum", date.today() - timedelta(days=1), key="end"
            )

        with col2:
            st.markdown("### 📜 Log-Fenster")
            log_container = st.empty()

        with col1:
            if st.button("🔄 Einmaliger Login"):
                driver = get_chrome_driver()
                driver.get(URL)
                log(
                    "🔐 Bitte im neuen Tab bei Google anmelden. Danach das Google-Tab schließen.",
                    "info",
                )
                time.sleep(60)
                save_cookies(driver)
                driver.quit()
                log("✅ Cookies erfolgreich gespeichert.", "success")
                show_log(log_container)  # Log aktualisieren NACH Aktion

            if st.button("🚀 Scraper ausführen"):
                run_all_scraper(start_date, end_date, log_container)
                show_log(log_container)  # Log aktualisieren NACH Aktion
                # Unsichtbarer minimaler Platzhalter (optional, falls du das brauchst)
                st.markdown('<div id="log-placeholder"></div>', unsafe_allow_html=True)

    # Logfenster **ganz unten** nur einmal rendern, initial leer
    show_log(log_container)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback

        traceback.print_exc()  # Stacktrace ausgeben
        input("Drücke Enter, um zu beenden…")
