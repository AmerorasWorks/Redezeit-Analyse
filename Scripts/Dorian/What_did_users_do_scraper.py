import time
from datetime import date, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.common.exceptions import TimeoutException
from csv_manager import CSVFileHandler

# ========== Kalenderhilfen ==========
GERMAN_MONTHS = {
    1: "JAN.", 2: "FEB.", 3: "MÄRZ", 4: "APR.",
    5: "MAI", 6: "JUNI", 7: "JULI", 8: "AUG.",
    9: "SEPT.", 10: "OKT.", 11: "NOV.", 12: "DEZ."
}
GERMAN_MONTHS_FOR_DAYS_BUTTON = {
    1: "Jan.", 2: "Feb.", 3: 'März', 4: "Apr.",
    5: "Mai", 6: "Juni", 7: "Juli", 8: "Aug.",
    9: "Sept.", 10: "Okt.", 11: "Nov.", 12: "Dez."
}
GERMAN_FULL_UPPER = {name.upper(): num for num, name in GERMAN_MONTHS.items()}


def click_day_button(cal_panel, target: date, wait: WebDriverWait):
    en_abbr = target.strftime("%b")
    de_full = GERMAN_MONTHS_FOR_DAYS_BUTTON[target.month]

    candidates = {
        f"{target.day} {en_abbr} {target.year}",
        f"{target.day} {de_full} {target.year}",
        f"{target.day}. {de_full} {target.year}",
    }

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.mat-calendar-body-cell")))
    cells = cal_panel.find_elements(By.CSS_SELECTOR, "button.mat-calendar-body-cell")

    for btn in cells:
        aria = btn.get_attribute("aria-label").strip()
        if aria in candidates:
            btn.click()
            return

    seen = [btn.get_attribute("aria-label").strip() for btn in cells]
    print("Versuchte Labels:", candidates)
    print("Gefundene: ", seen)
    raise RuntimeError("Datum nicht gefunden im Kalender")


def get_current_year_month(cal_panel):
    raw = cal_panel.find_element(By.CSS_SELECTOR, ".mat-calendar-period-button").text.strip().upper().rstrip(".")
    month_str, year_str = raw.split()
    return int(year_str), GERMAN_FULL_UPPER[month_str]


def select_date_range(driver, start: date, end: date):
    wait = WebDriverWait(driver, 10)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.canvas-date-input"))).click()
    calendars = wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".mat-calendar")))
    start_cal, end_cal = calendars

    def click_until(direction: str, cal_panel, target_header):
        btn = cal_panel.find_element(By.CSS_SELECTOR, f"button.mat-calendar-{direction}-button")
        header_sel = (By.CSS_SELECTOR, ".mat-calendar-period-button")
        for _ in range(48):
            header = cal_panel.find_element(*header_sel).text.strip().upper()
            if header == target_header:
                return
            btn.click()
            wait.until(lambda d: cal_panel.find_element(*header_sel).text.strip().upper() != header)

    start_header = f"{GERMAN_MONTHS[start.month]} {start.year}"
    end_header = f"{GERMAN_MONTHS[end.month]} {end.year}"

    if get_current_year_month(start_cal) < (start.year, start.month):
        click_until("next", start_cal, start_header)
    else:
        click_until("previous", start_cal, start_header)

    if get_current_year_month(end_cal) < (end.year, end.month):
        click_until("next", end_cal, end_header)
    else:
        click_until("previous", end_cal, end_header)

    click_day_button(start_cal, start, wait)
    click_day_button(end_cal, end, wait)

    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.apply-button"))).click()


# ========== Tabellendaten scrapen ==========
def extract_table_data(driver, date_str: str):
    wait = WebDriverWait(driver, 10)
    data = []
    seen_fingerprints = set()

    def get_cells():
        all_tables = driver.find_elements(By.CSS_SELECTOR, ".table")
        last_table = all_tables[-1]
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
            if len(row) == 5:
                entry = {
                    "Datum": date_str,
                    "EID": row[0],
                    "Name des Events": row[1],
                    "event_label": row[2],
                    "Aktive Nutzer": row[3].replace(".", "").replace(",", "."),
                    "Ereignisanzahl": row[4].replace(".", "").replace(",", "."),
                }
                data.append(entry)
                row = []

        # Versuch, zur nächsten Seite zu wechseln
        try:
            prev_first_cell = cells[0].text.strip()

            next_btn = driver.find_element(By.CSS_SELECTOR, ".pageForward")
            if "disabled" in next_btn.get_attribute("class").lower():
                print("✅ Letzte Seite erreicht.")
                break

            driver.execute_script("arguments[0].click();", next_btn)

            # Warte, bis sich Inhalt geändert hat
            WebDriverWait(driver, 10).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, "div.cell")[0].text.strip() != prev_first_cell
            )
            time.sleep(5)

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
    driver.get(url)
    return driver


# ========== Main ==========
if __name__ == '__main__':
    url = "https://lookerstudio.google.com/u/0/reporting/3c1fa903-4f31-4e6f-9b54-f4c6597ffb74/page/4okDC"
    csv_handler = CSVFileHandler("../../Data/Scrapping data as csv/what_did_users_do2.csv", headers=["Datum", "EID", "Name des Events", "event_label", "Aktive Nutzer", "Ereignisanzahl"])
    driver = init_driver(url)
    input("🔐 Bitte im geöffneten Fenster anmelden und zur Tabelle scrollen. Danach hier Enter drücken ...")

    start_date = date(2024, 5, 2)
    end_date =  date(2024, 5, 2)
    current_date = start_date

    while current_date <= end_date:
        print(f"\n📆 Datum wählen: {current_date}")
        try:
            select_date_range(driver, current_date, current_date)
            time.sleep(5)
            date_str = current_date.isoformat()
            table_data = extract_table_data(driver, date_str)

            for row in table_data:
                csv_handler.append_row(row)
        except Exception as e:
            print(f"⚠️ Fehler am {current_date}: {e}")
        current_date += timedelta(days=1)

    driver.quit()
