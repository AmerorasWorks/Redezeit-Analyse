import time
from datetime import date, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from Scripts.Dorian.utils.csv_manager import CSVFileHandler
from Scripts.Dorian.utils.kalender_funktion import select_date_range


# ========== Tabellendaten scrapen ==========

def extract_landingpage_data(driver, date_str: str):
    wait = WebDriverWait(driver, 10)
    data = []
    seen_fingerprints = set()

    def get_cells():
        all_tables = driver.find_elements(By.CSS_SELECTOR, ".table")
        last_table = all_tables[1]
        return last_table.find_elements(By.CSS_SELECTOR, "div.cell")

    while True:
        cells = get_cells()
        print(f"📦 {len(cells)} Zellen erkannt (Seite).")

        # Fingerprint der Seite (ersten 10 Zelltexte)
        fingerprint = tuple(cell.text.strip() for cell in cells[:10])
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
                    "Aufrufe": row[2].replace(".", "").replace(",", ".")
                }
                data.append(entry)
                row = []

        # Versuch, zur nächsten Seite zu wechseln
                # Versuch, zur nächsten Seite zu wechseln
                try:
                    prev_first_cell_text = cells[0].text.strip()

                    next_btn = driver.find_element(By.CSS_SELECTOR, ".pageForward")
                    if "disabled" in next_btn.get_attribute("class").lower():
                        print("✅ Letzte Seite erreicht.")
                        break

                    driver.execute_script("arguments[0].click();", next_btn)

                    # Warte auf neue Seite: cells[0] neu ermitteln, nicht stale!
                    WebDriverWait(driver, 10).until(
                        lambda d: d.find_elements(By.CSS_SELECTOR, "div.cell") and
                                d.find_elements(By.CSS_SELECTOR, "div.cell")[0].text.strip() != prev_first_cell_text
                    )

                    time.sleep(5)  # optional: kurz warten, bis Rendering fertig ist

                except TimeoutException:
                    print("⚠️ Timeout beim Seitenwechsel: Inhalt unverändert.")
                    break
                except NoSuchElementException:
                    print("❌ Weiter-Button nicht gefunden – wahrscheinlich letzte Seite.")
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
    #driver.maximize_window()
    driver.get(url)
    return driver


# ========== Main ==========

if __name__ == '__main__':
    url = "https://lookerstudio.google.com/u/0/reporting/3c1fa903-4f31-4e6f-9b54-f4c6597ffb74/page/4okDC"
    csv_handler = CSVFileHandler("../../Data/Scrapping data as csv/landingpage.csv",
                                headers=["Datum",
                                        "EID",
                                        "Seitentitel",
                                        "Aufrufe"]
                                )
    driver = init_driver(url)
    input("🔐 Bitte im geöffneten Fenster anmelden und zur Tabelle scrollen. Danach hier Enter drücken ...")

    start_date = date(2023,1,1)
    yesterday = date.today()
    yesterday -= timedelta(days=1)
    print (f"Anfangsdatum: {start_date}\nEnddatum: {yesterday}")
    current_date = start_date

    while current_date <= yesterday:
        print(f"\n📆 Datum wählen: {current_date}")
        try:
            select_date_range(driver, current_date, current_date)
            time.sleep(5)
            date_str = current_date.isoformat()
            table_data = extract_landingpage_data(driver, date_str)

            for row in table_data:
                csv_handler.append_row(row)
        except Exception as e:
            print(f"⚠️ Fehler am {current_date}: {e}")
        current_date += timedelta(days=1)

    driver.quit()
