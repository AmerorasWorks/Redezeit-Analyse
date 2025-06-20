import time
from datetime import date, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from kalender_funktion import select_date_range
from csv_manager import CSVFileHandler



# ========== Tabellendaten scrapen ==========

'''Hier lesen wir die ersten 5 Daten aus (User behaviour)
Kann man über CSS machen durch die div, die value-laben heißt.
Falls keine Daten sammelbar sind, steht "Keine Daten" im HTML. Das benutzen wir um Fehler zu begehen
Danach speichern wir alles auf eine Dictionary und geben diese Dictionary zurück.'''

def user_behaviour(driver, date: date) -> dict | None:
    value_labels = driver.find_elements(By.CSS_SELECTOR, "div.value-label")

    if value_labels[0].text == "Keine Daten":
        print(f"Keine Daten sammelbar (Feiertag o.ä.) für {date}")
        return None

    # Müssen Kommas mit Punkten ersetzen (da CSV!!!).
    # Absprungsrate hat Leerzeichen vor "%". Muss auch abgekürzt werden. (2,05 % -> 2.05%)
    user_behaviour_dict = {
        "Datum": date,
        "Seitenaufrufe": value_labels[0].text,
        "Nutzer Insgesamt": value_labels[1].text,
        "Durchschn. Zeit auf der Seite": value_labels[2].text,
        "Absprungrate": value_labels[3].text.replace(",", ".").replace(" ", ""),
        "Seiten / Sitzung": value_labels[4].text.replace(',', "."),
    }
    return user_behaviour_dict


# ========== Chrome Initialisierung ==========

def init_driver(url: str):
    service = Service()
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    driver.get(url)
    return driver


# ========= Main ==========

if __name__ == '__main__':
    redezeit_url = "https://lookerstudio.google.com/u/0/reporting/3c1fa903-4f31-4e6f-9b54-f4c6597ffb74/page/4okDC"
    csv_handler = CSVFileHandler("../../Data/Scrapping data as csv/user_behaviors.csv", headers=["Datum", "Seitenaufrufe", "Nutzer Insgesamt", "Durchschn. Zeit auf der Seite", "Absprungrate", "Seiten / Sitzung"])
    driver = init_driver(redezeit_url)

    #Datenangabe von wann bis wann wir die Daten auslesen wollen
    #Enddatum muss "Gestern" sein, da die heutigen Daten noch gesammelt werden.
    start_date = date(2025,6,18)
    yesterday = date.today()
    yesterday -= timedelta(days=1)
    print (f"Anfangsdatum: {start_date}\nEnddatum: {yesterday}")
    current_date = start_date


    # Loop von 2023-01-01 bis gestern.
    '''Wir wählen das Datum aus und lassen die Daten für X Sekunden laden mit einem "Sleep"
    Danach lesen wir die Daten aus und falls es nicht "None" ist (also nicht "Keine Daten"), speichern wir es
    in unserer CSV ab und inkrementieren den Tag um 1 bis wir am Enddatum ankommen.'''

    while current_date <= yesterday:
        print(f"Getting data for Day: {current_date}.")
        select_date_range(driver, current_date, current_date)
        time.sleep(10)
        user_behaviour = user_behaviour(driver, current_date)
        if user_behaviour:
            csv_handler.append_row(user_behaviour)

        current_date += timedelta(days=1)
