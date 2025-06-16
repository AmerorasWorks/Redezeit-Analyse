import time
from datetime import date, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from csv_manager import CSVFileHandler

# Braucht man um im Kalender den richtigen Monat zu picken (Wenn Webseite auf Deutsch ist)
GERMAN_MONTHS = {
    1: "JAN.",  2: "FEB.",  3: "MÄRZ",   4: "APR.",
    5: "MAI",  6: "JUNI", 7: "JULI",   8: "AUG.",
    9: "SEPT.",10: "OKT.", 11: "NOV.",   12: "DEZ."
}

# Braucht man um im Kalender den richtigen Tag zu Wählen
GERMAN_MONTHS_FOR_DAYS_BUTTON = {
    1: "Jan.",  2: "Feb.",  3: "März'",   4: "Apr.",
    5: "Mai",  6: "Juni", 7: "Juli",   8: "Aug.",
    9: "Sept.",10: "Okt.", 11: "Nov.",   12: "Dez."
}

# Braucht man um Kalendermonat zu berechnen
GERMAN_FULL_UPPER = {name.upper(): num for num, name in GERMAN_MONTHS.items()}

# Funktion um nur den Tag anzuklicken.
# Im HTML gibt es eine "aria-label", die das Datum abspeichert im Format "Tag Monat Jahr"
# Das kann aber in Englisch, Deutsch, oder auch Deutsch mit "." nach dem Tag sein (also "Tag. Monat Jahr")
# Wir checken alle Kandidaten ab und dann wählen wir den Tag aus wenn wir es finden.
# Falls der Tag nicht gefunden wird, geben wir ein Error aus für Debugzwecke.
# Debug: Welche Tage haben wir versucht und welche haben wir tatsächlich bekommen.
def click_day_button(cal_panel, target: date, wait: WebDriverWait):
    en_abbr = target.strftime("%b")
    de_full = GERMAN_MONTHS_FOR_DAYS_BUTTON[target.month]

    candidates = {
        f"{target.day} {en_abbr} {target.year}",
        f"{target.day} {de_full} {target.year}",
        f"{target.day}. {de_full} {target.year}",
    }

    wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "button.mat-calendar-body-cell")
    ))

    cells = cal_panel.find_elements(By.CSS_SELECTOR, "button.mat-calendar-body-cell")

    for btn in cells:
        aria = btn.get_attribute("aria-label").strip()
        if aria in candidates:
            btn.click()
            return

    # Debug
    seen = [btn.get_attribute("aria-label").strip() for btn in cells]
    print("Versuchte Labels:", candidates)
    print("Gefundene: ", seen)
    raise RuntimeError("Code geht nicht")

# Wir unpacken den header (*) und vom header kriegen wir das Raw element für den Monat & Jahr
# Diesen splitten wir und "konvertieren" es in ein Deutsches Layout für spätere Nutzung
def get_current_year_month(cal_panel):
        header_locator = (By.CSS_SELECTOR, ".mat-calendar-period-button")
        raw = cal_panel.find_element(*header_locator).text.strip().upper().rstrip(".")
        month_str, year_str = raw.split()
        month = GERMAN_FULL_UPPER[month_str]
        year = int(year_str)
        return year, month

# Methode um ein Datum zu picken. Wir können mit Selenium simulieren, dass wir im Datumpicker uns hin- und her bewegen.
# Dazu öffnen wir den date-picker nachdem die Webseite bereit ist und initialisieren den linken und rechten Kalender
# Danach berechnen wir, wo wir uns im Kalender befinden
# Letztlich navigieren wir nach vorne oder nach hinten und simulieren ein "Anwenden" Button Click
def select_date_range(driver, start: date, end: date):
    wait = WebDriverWait(driver, 10)

    # Kalender öffnen
    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "button.canvas-date-input")
    )).click()

    # Beide Kalender auswählen
    calendars = wait.until(EC.visibility_of_all_elements_located(
        (By.CSS_SELECTOR, ".mat-calendar")
    ))
    start_cal, end_cal = calendars

    # Methode, die definiert, wie oft wir in welche Richtung klicken.
    def click_until(previous_or_next: str, cal_panel, target_header):
        prev_or_next_btn = cal_panel.find_element(
            By.CSS_SELECTOR, f"button.mat-calendar-{previous_or_next}-button"
        )
        header_selector = (By.CSS_SELECTOR, ".mat-calendar-period-button")

        for _ in range(48):  # Maximal 4 Jahre Suche
            header_text = cal_panel.find_element(*header_selector).text.strip().upper()
            if header_text == target_header:
                return
            prev_or_next_btn.click()

            # Warten, bis header wechselt bis man weiter klickt
            wait.until(lambda d:
                cal_panel.find_element(*header_selector).text.strip().upper() != header_text
            )
        raise RuntimeError(f"Could not navigate to month '{target_header}'")

    start_header = f"{GERMAN_MONTHS[start.month]} {start.year}"
    end_header   = f"{GERMAN_MONTHS[end.month]} {end.year}"

    # Navigieren beider Kalender
    current_year = get_current_year_month(start_cal)
    target_year_month_start = (start.year, start.month)
    if current_year < target_year_month_start:
        click_until("next", start_cal, start_header)
    elif current_year > target_year_month_start:
        click_until("previous", start_cal, start_header)

    current_year = get_current_year_month(end_cal)
    target_year_month_start = (end.year, end.month)
    if current_year < target_year_month_start:
        click_until("next", end_cal, end_header)
    elif current_year > target_year_month_start:
        click_until("previous", end_cal, end_header)

    # Tage anklicken
    click_day_button(start_cal, start, wait)
    click_day_button(end_cal, end, wait)

    # Anwenden anklicken
    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "button.apply-button")
    )).click()

# Hier lesen wir die ersten 5 Daten aus (User behaviour)
# Kann man über CSS machen durch die div, die value-laben heißt.
# Falls keine Daten sammelbar sind, steht "Keine Daten" im HTML. Das benutzen wir um Fehler zu begehen
# Danach speichern wir alles auf eine Dictionary und geben diese Dictionary zurück.
def read_value_user_behaviour(driver, date: date) -> dict | None:
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

# Driver initialisieren
def init_driver(url: str):
    service = Service()
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    return driver

# Main Methode, die den Loop ausführt
if __name__ == '__main__':
    redezeit_url = "https://lookerstudio.google.com/u/0/reporting/3c1fa903-4f31-4e6f-9b54-f4c6597ffb74/page/4okDC"
    csv_handler = CSVFileHandler("output.csv", headers=["Datum", "Seitenaufrufe", "Nutzer Insgesamt", "Durchschn. Zeit auf der Seite", "Absprungrate", "Seiten / Sitzung"])
    driver = init_driver(redezeit_url)

    # Datenangabe von wann bis wann wir die Daten auslesen wollen
    # Enddatum muss "Gestern" sein, da die heutigen Daten noch gesammelt werden.
    start_date = date(2023,1,1)
    yesterday = date.today()
    yesterday -= timedelta(days=1)
    print (f"Anfangsdatum: {start_date}\nEnddatum: {yesterday}")
    current_date = start_date

    # Loop von 2023-01-01 bis gestern.
    # Wir wählen das Datum aus und lassen die Daten für X Sekunden laden mit einem "Sleep"
    # Danach lesen wir die Daten aus und falls es nicht "None" ist (also nicht "Keine Daten"), speichern wir es
    # in unserer CSV ab und inkrementieren den Tag um 1 bis wir am Enddatum ankommen.
    while current_date <= yesterday:
        print(f"Getting data for Day: {current_date}.")
        select_date_range(driver, current_date, current_date)
        time.sleep(5)
        user_behaviour = read_value_user_behaviour(driver, current_date)
        if user_behaviour:
            csv_handler.append_row(user_behaviour)

        current_date += timedelta(days=1)
