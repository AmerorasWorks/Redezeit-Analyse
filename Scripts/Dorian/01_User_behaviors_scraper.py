import time
from datetime import date, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from Scripts.Dorian.utils.kalender_funktion import select_date_range
from Scripts.Dorian.utils.csv_manager import CSVFileHandler


# ========== Daten extrahieren ==========

def extract_user_behaviour(driver, date_obj: date) -> dict | None:
    try:
        wait = WebDriverWait(driver, 10)
        value_labels = driver.find_elements(By.CSS_SELECTOR, "div.value-label")

        if not value_labels:
            print(f"⚠️ Keine Labels gefunden für {date_obj}")
            return None

        if value_labels[0].text.strip() == "Keine Daten":
            print(f"🛑 Keine Daten sammelbar (Feiertag o.ä.) für {date_obj}")
            return None

        print(f"📊 Daten extrahiert für {date_obj}")

        return {
            "Datum": date_obj.isoformat(),
            "Seitenaufrufe": value_labels[0].text,
            "Nutzer Insgesamt": value_labels[1].text,
            "Durchschn. Zeit auf der Seite": value_labels[2].text,
            "Absprungrate": value_labels[3].text.replace(",", ".").replace(" ", ""),
            "Seiten / Sitzung": value_labels[4].text.replace(",", "."),
        }

    except Exception as e:
        print(f"❌ Fehler beim Extrahieren der Daten am {date_obj}: {e}")
        return None


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
    csv_handler = CSVFileHandler(
        "../../Data/Scrapping data as csv/user_behaviors.csv",
        headers=["Datum",
                "Seitenaufrufe",
                "Nutzer Insgesamt",
                "Durchschn. Zeit auf der Seite",
                "Absprungrate", "Seiten / Sitzung"]
    )

    driver = init_driver(url)
    input("🔐 Bitte im geöffneten Fenster anmelden und zur Tabelle scrollen. Danach hier Enter drücken ...")

    start_date = date(2023, 1, 1)
    end_date = date.today() - timedelta(days=1)
    print(f"📅 Zeitraum: {start_date} bis {end_date}")

    current_date = start_date

    while current_date <= end_date:
        print(f"\n📆 Datum wählen: {current_date}")
        try:
            select_date_range(driver, current_date, current_date)
            time.sleep(10)
            data = extract_user_behaviour(driver, current_date)
            if data:
                csv_handler.append_row(data)
        except Exception as e:
            print(f"⚠️ Fehler am {current_date}: {e}")
        current_date += timedelta(days=1)

    driver.quit()
    print("✅ Alle Daten extrahiert und gespeichert.")
