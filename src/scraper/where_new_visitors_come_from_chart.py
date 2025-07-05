import time
from datetime import date, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)
from bs4 import BeautifulSoup
from src.utils.csv_manager_utils import CSVFileHandler
from src.utils.calender_utils import select_date_range

# ========== Tabellendaten für "piechart gviz" extrahieren ==========


def extract_table_for_piechart_gviz(driver, date_str):
    """
    Extrahiert die Tabelle des ersten Diagramms mit class "piechart gviz".
    Gibt Liste von Dicts zurück: [{"Datum", "Kategorie", "Wert"}, ...]
    """
    soup = BeautifulSoup(driver.page_source, "html.parser")
    components = soup.find_all(
        "ng2-piechart-component", class_="piechart gviz selectable"
    )
    if not components:
        print("❌ Keine Komponente mit class 'piechart gviz selectable' gefunden.")
        return []

    # Falls mehrere, nimm das erste (bzw. Index anpassen!)
    comp = components[0]
    table_div = comp.find(
        "div", attrs={"aria-label": lambda x: x and "tabellarische Darstellung" in x}
    )
    if table_div is None:
        print("❌ Keine Tabelle im Diagramm gefunden.")
        return []

    table = table_div.find("table")
    if table is None:
        print("❌ Keine <table> gefunden.")
        return []

    # Zeilen extrahieren (ab Zeile 1, weil Zeile 0 der Header ist)
    data = []
    for tr in table.find_all("tr")[1:]:
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue
        data.append(
            {
                "datum": date_str,
                "kategorie": tds[0].text.strip(),
                "wert": tds[1].text.strip(),
            }
        )
    print(f"✅ {len(data)} Zeilen aus Where_They_Come_From-Chart extrahiert.")
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
    url = "https://lookerstudio.google.com/u/0/reporting/3c1fa903-4f31-4e6f-9b54-f4c6597ffb74/page/4okDC"  # <-- Anpassen!
    csv_handler = CSVFileHandler(
        "exported_data/where_new_visitors_come_from_chart.csv",
        headers=["Datum", "Kategorie", "Wert"],
    )

    driver = init_driver(url)
    input(
        "🔐 Bitte im geöffneten Fenster anmelden und zur richtigen Seite scrollen. Danach hier Enter drücken ..."
    )

    start_date = date(2023, 1, 1)
    end_date = date.today() - timedelta(days=1)
    print(f"📅 Zeitraum: {start_date} bis {end_date}")

    current_date = start_date
    while current_date <= end_date:
        print(f"\n📆 Datum wählen: {current_date}")
        try:
            select_date_range(driver, current_date, current_date)
            time.sleep(8)  # Wartezeit fürs Laden

            rows = extract_table_for_piechart_gviz(driver, current_date.isoformat())
            for row in rows:
                csv_handler.append_row(row)
        except Exception as e:
            print(f"⚠️ Fehler am {current_date}: {e}")
        current_date += timedelta(days=1)

    driver.quit()
    print("✅ Alle Daten extrahiert und gespeichert.")
