import streamlit as st
from datetime import date, timedelta
import pickle
import os
import sys
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
SCRAPE_LOG_PATH = os.path.join("src", "Data", "log", "scrape_log.csv")

# Lokale Tools (du musst sicherstellen, dass diese Module im selben Ordner liegen oder per sys.path importierbar sind)
sys.path.append(os.path.dirname(__file__))

from src.utils.kalender_funktion import select_date_range
from src.utils.csv_manager import CSVFileHandler

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


COOKIE_PATH = resource_path("src/cookies/cookies.pkl")
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


# === Initialisiere Chrome mit gespeicherten CookiesCookies ===
def init_driver_with_cookies():
    # Bundled chromedriver.exe finden
    chrome_path = resource_path("chromedriver.exe")
    service = Service(executable_path=chrome_path)

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(URL)

    if os.path.exists(COOKIE_PATH):
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
    cookies = driver.get_cookies()
    with open(COOKIE_PATH, "wb") as f:
        pickle.dump(cookies, f)


# === Alle Scraper ausführen ===
def run_all_scraper(start_date, end_date):
    driver = init_driver_with_cookies()

    # Ordner für Kalenderwoche erstellen
    year, kw, _ = start_date.isocalendar()
    output_folder = os.path.join("src", "Data")
    os.makedirs(output_folder, exist_ok=True)

    current = start_date
    while current <= end_date:
        if is_date_scraped(current):
            st.info(f"📅 {current.isoformat()} schon gescrapt – überspringe.")
            current += timedelta(days=1)
            continue

        st.write(f"\n📆 Scraping für {current.isoformat()}")
        try:
            select_date_range(driver, current, current)
            time.sleep(8)

            # Landingpage
            data = extract_landingpage_data(driver, current.isoformat())
            lp_csv = CSVFileHandler(
                os.path.join(output_folder, f"landingpage.csv"),
                headers=["Datum", "EID", "Seitentitel", "Aufrufe"],
            )
            for row in data:
                lp_csv.append_row(row)

            # User Behaviour
            row = extract_user_behaviour(driver, current)
            if row:
                ub_csv = CSVFileHandler(
                    os.path.join(output_folder, f"user_behaviors.csv"),
                    headers=[
                        "Datum",
                        "Seitenaufrufe",
                        "Nutzer Insgesamt",
                        "Durchschn. Zeit auf der Seite",
                        "Absprungrate",
                        "Seiten / Sitzung",
                    ],
                )
                ub_csv.append_row(row)

            # Events
            data = extract_events_data(driver, current.isoformat())
            ev_csv = CSVFileHandler(
                os.path.join(output_folder, f"what_did_user_do.csv"),
                headers=[
                    "Datum",
                    "EID",
                    "Name des Events",
                    "even_label",
                    "Aktive Nutzer",
                    "Ereignisanzahl",
                ],
            )
            for row in data:
                ev_csv.append_row(row)

            # Quellen Tabelle
            data = extract_sources_data(driver, current.isoformat())
            src_csv = CSVFileHandler(
                os.path.join(output_folder, f"where_did_they_come_from.csv"),
                headers=[
                    "Datum",
                    "EID",
                    "Quelle",
                    "Sitzungen",
                    "Aufrufe",
                    "Aufrufe pro Sitzung",
                ],
            )
            for row in data:
                src_csv.append_row(row)

            # Piecharts:
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
                    headers=["Datum", "Kategorie", "Wert"],
                )
                for row in pie_data:
                    pie_csv.append_row(row)

        except Exception as e:
            st.error(f"❌ Fehler am {current}: {e}")
        else:
            # 2) Erfolgreiches Scrapen loggen
            log_scraped_date(current)
            st.success(f"✅ {current.isoformat()} geloggt.")
        finally:
            current += timedelta(days=1)

    driver.quit()
    st.success("✅ Alle Scraper erfolgreich abgeschlossen!")


# Load CSS file
load_custom_css("style.css")


# === Streamlit UI ===
def main():
    # === CSS hier ganz oben laden ===
    load_custom_css("style.css")

    st.header("scrapetime")
    st.subheader("Willkommen beim Redezeit-Scraping-Tool!")
    st.text(
        "Hier kannst du Daten vom Redezeit-Dashboard extrahieren und in CSV-Dateien speichern. \n"
        "Bitte beachte, dass du dich einmalig bei Google anmelden musst, um die Cookies zu speichern. \n"
        "Danach kannst du die Scraper für einen bestimmten Zeitraum ausführen."
    )

    start_date = st.date_input("Startdatum", date.today() - timedelta(days=7))
    end_date = st.date_input("Enddatum", date.today() - timedelta(days=1))

    if st.button("🔄 Login & Cookies speichern (nur beim 1. anmelden notwendig!)"):
        driver = webdriver.Chrome(service=Service(), options=webdriver.ChromeOptions())
        chrome_path = resource_path("chromedriver.exe")
        driver = webdriver.Chrome(
            service=Service(executable_path=chrome_path),
            options=webdriver.ChromeOptions(),
        )
        driver.get(URL)
        st.info(
            "🔐 Bitte im neuem Tab bei Google anmelden. Danach das Google-Tab schließen."
        )
        time.sleep(60)
        save_cookies(driver)
        driver.quit()
        st.success("✅ Cookies erfolgreich gespeichert.")

    if st.button("🚀 Alle Scraper ausführen!"):
        run_all_scraper(start_date, end_date)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback

        traceback.print_exc()  # Stacktrace ausgeben
        input("Drücke Enter, um zu beenden…")
