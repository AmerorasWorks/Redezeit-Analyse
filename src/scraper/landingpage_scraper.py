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

    def get_cells():
        all_tables = driver.find_elements(By.CSS_SELECTOR, ".table")
        if len(all_tables) < 3:
            raise Exception("❌ Erwartete Tabelle (Index 2) nicht gefunden.")
        last_table = all_tables[1]
        return last_table.find_elements(By.CSS_SELECTOR, "div.cell")

    def safe_get_cells(retries=5, delay=1):
        for attempt in range(retries):
            try:
                return get_cells()
            except StaleElementReferenceException:
                print(f"⚠️ Stale bei get_cells – Versuch {attempt + 1}")
                time.sleep(delay)
        raise Exception("❌ 5x StaleElement bei get_cells – Abbruch.")

    def get_fingerprint(cells):
        return tuple(cell.text.strip() for cell in cells[:10])

    def wait_for_page_change(driver, old_fingerprint):
        def changed(d):
            try:
                new_cells = safe_get_cells()
                if len(new_cells) < 10:
                    return False
                return get_fingerprint(new_cells) != old_fingerprint
            except:
                return False

        wait.until(changed)

    while True:
        try:
            cells = safe_get_cells()
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
        for cell in cells:
            text = cell.text.strip()
            if not text:
                continue
            row.append(text)
            if len(row) == 3:
                entry = {
                    "Datum": date_str,
                    "EID": row[0],
                    "Seitentitel": row[1],
                    "Aufrufe": row[2],
                }
                data.append(entry)
                row = []

        try:
            all_tables = driver.find_elements(By.CSS_SELECTOR, ".table")
            target_table = all_tables[1]
            next_btn = target_table.find_element(By.CSS_SELECTOR, ".pageForward")

            if "disabled" in next_btn.get_attribute("class").lower():
                print("✅ Letzte Seite erreicht.")
                break

            driver.execute_script("arguments[0].click();", next_btn)
            wait_for_page_change(driver, fingerprint)
            time.sleep(2)

        except (StaleElementReferenceException, TimeoutException) as e:
            print(f"⚠️ Fehler beim Blättern: {e}")
            break
        except NoSuchElementException:
            print("❌ Weiter-Button fehlt – vermutlich letzte Seite.")
            break
        except Exception as e:
            print(f"⚠️ Unerwarteter Fehler beim Blättern: {e}")
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
        "../../../Data/Scrapping data as csv/landingpage.csv",
        headers=["Datum", "EID", "Seitentitel", "Aufrufe"],
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
            print("⏳ Warte auf das Neuladen der Tabelle ...")
            time.sleep(8)  # zusätzliche Wartezeit für vollständiges Laden

            table_data = extract_table_data(driver, current_date.isoformat())
            for row in table_data:
                csv_handler.append_row(row)
        except Exception as e:
            print(f"⚠️ Fehler am {current_date}: {e}")
        current_date += timedelta(days=1)

    driver.quit()
    print("✅ Alle Daten extrahiert und gespeichert.")
