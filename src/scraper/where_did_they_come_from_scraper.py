import time
from datetime import date, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)
from src.utils.csv_manager import CSVFileHandler
from src.utils.kalender_funktion import select_date_range


# ========== Tabellendaten scrapen ==========


def extract_table_data(driver, date_str: str):
    wait = WebDriverWait(driver, 10)
    data = []
    seen_fingerprints = set()

    def get_tables():
        # Versuche mehrfach, Tabellen stabil zu holen
        for _ in range(5):
            try:
                tables = driver.find_elements(By.CSS_SELECTOR, ".table")
                if len(tables) < 4:
                    raise Exception("❌ Erwartete Tabelle (Index 3) nicht gefunden.")
                return tables
            except StaleElementReferenceException:
                time.sleep(5)
        raise Exception("❌ Tabellen konnten nicht stabil geladen werden.")

    def get_cells():
        # Nutzt get_tables für stabilen Zugriff
        tables = get_tables()
        last_table = tables[3]
        for _ in range(5):
            try:
                cells = last_table.find_elements(By.CSS_SELECTOR, "div.cell")
                return cells
            except StaleElementReferenceException:
                time.sleep(5)
                tables = get_tables()  # nochmal komplette Tabellen neu holen
                last_table = tables[3]
        raise Exception("❌ Zellen konnten nicht stabil geladen werden.")

    def get_fingerprint(cells):
        # Fingerprint zur Seitenerkennung (erst 10 Zellen)
        return tuple(cell.text.strip() for cell in cells[:10])

    def wait_for_page_change(driver, old_fingerprint, timeout=10):
        wait = WebDriverWait(driver, timeout)

        def changed(d):
            try:
                new_cells = get_cells()
                if len(new_cells) < 10:
                    return False
                return get_fingerprint(new_cells) != old_fingerprint
            except StaleElementReferenceException:
                return False

        wait.until(changed)

    while True:
        try:
            cells = get_cells()
        except Exception as e:
            print(f"❌ Fehler beim Lesen der Zellen: {e}")
            break

        print(f"📦 {len(cells)} Zellen erkannt (Seite).")

        fingerprint = get_fingerprint(cells)
        if fingerprint in seen_fingerprints:
            print("🔁 Wiederholte Seite erkannt – Abbruch der Schleife.")
            break
        seen_fingerprints.add(fingerprint)

        row = []
        for i in range(len(cells)):
            # Hole Zellen-Text in robustem try-except mit Neuversuchen
            for attempt in range(5):
                try:
                    current_cells = get_cells()
                    text = current_cells[i].text.strip()
                    break
                except StaleElementReferenceException:
                    time.sleep(5)
                    if attempt == 4:
                        print(
                            "❌ StaleElementReferenceException: Zelle konnte nicht stabil gelesen werden."
                        )
                        text = ""
            if not text:
                continue
            row.append(text)
            if len(row) == 5:
                entry = {
                    "Datum": date_str,
                    "EID": row[0],
                    "Quelle": row[1],
                    "Sitzungen": row[2],
                    "Aufrufe": row[3],
                    "Aufrufe pro Sitzung": row[4].replace(".", "").replace(",", "."),
                }
                data.append(entry)
                row = []

        # Robust zum Weiter-Button und Seitenwechsel:
        try:
            tables = get_tables()
            target_table = tables[3]

            # Button mehrfach versuchen zu holen und klicken
            next_btn = None
            for _ in range(5):
                try:
                    next_btn = target_table.find_element(
                        By.CSS_SELECTOR, ".pageForward"
                    )
                    break
                except StaleElementReferenceException:
                    time.sleep(5)
                    tables = get_tables()
                    target_table = tables[3]

            if next_btn is None:
                print("❌ Weiter-Button nicht gefunden, Ende der Seiten.")
                break

            if "disabled" in next_btn.get_attribute("class").lower():
                print("✅ Letzte Seite erreicht.")
                break

            # Klick robust per execute_script mit Wiederholung
            for _ in range(3):
                try:
                    driver.execute_script("arguments[0].click();", next_btn)
                    break
                except StaleElementReferenceException:
                    time.sleep(5)
                    tables = get_tables()
                    target_table = tables[3]
                    next_btn = target_table.find_element(
                        By.CSS_SELECTOR, ".pageForward"
                    )

            wait_for_page_change(driver, fingerprint)
            time.sleep(5)

        except TimeoutException:
            print("⚠️ Timeout beim Seitenwechsel: Inhalt unverändert.")
            break
        except (NoSuchElementException, StaleElementReferenceException) as e:
            print(f"❌ Weiter-Button-Fehler – wahrscheinlich letzte Seite: {e}")
            break
        except Exception as e:
            print(f"⚠️ Fehler beim Blättern: {e}")
            break

    print(f"✅ {len(data)} Datensätze insgesamt extrahiert.")
    return data


# ========== Chrome Initialisierung ==========


def init_driver(url: str):
    service = Service()
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    return driver


# ========== Main ==========

if __name__ == "__main__":
    url = "https://lookerstudio.google.com/u/0/reporting/3c1fa903-4f31-4e6f-9b54-f4c6597ffb74/page/4okDC"
    csv_handler = CSVFileHandler(
        "../../Data/Scrapping data as csv/where_did_they_come_from.csv",
        headers=[
            "Datum",
            "EID",
            "Quelle",
            "Sitzungen",
            "Aufrufe",
            "Aufrufe pro Sitzung",
        ],
    )

    driver = init_driver(url)
    input(
        "🔐 Bitte im geöffneten Fenster anmelden und zur Tabelle scrollen. Danach hier Enter drücken ..."
    )

    start_date = date(2023, 1, 1)
    end_date = date.today() - timedelta(days=1)
    print(f"📅 Zeitraum: {start_date} bis {end_date}")

    current_date = start_date
    while current_date <= end_date:
        print(f"\n📆 Datum wählen: {current_date}")
        try:
            select_date_range(driver, current_date, current_date)
            time.sleep(5)
            table_data = extract_table_data(driver, current_date.isoformat())
            for row in table_data:
                csv_handler.append_row(row)
        except Exception as e:
            print(f"⚠️ Fehler am {current_date}: {e}")
        current_date += timedelta(days=1)

    driver.quit()
    print("✅ Alle Daten extrahiert und gespeichert.")
