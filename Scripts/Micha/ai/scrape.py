import selenium.webdriver as webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import date, timedelta
import time
from bs4 import BeautifulSoup

# Kalenderlogik
GERMAN_MONTHS = {
    1: "JAN.",  2: "FEB.",  3: "MÄRZ",   4: "APR.",
    5: "MAI",  6: "JUNI", 7: "JULI",   8: "AUG.",
    9: "SEPT.",10: "OKT.", 11: "NOV.",   12: "DEZ."
}

GERMAN_MONTHS_FOR_DAYS_BUTTON = {
    1: "Jan.",  2: "Feb.",  3: 'März',   4: "Apr.",
    5: "Mai",  6: "Juni", 7: "Juli",   8: "Aug.",
    9: "Sept.",10: "Okt.", 11: "Nov.",   12: "Dez."
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

    wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "button.mat-calendar-body-cell")
    ))

    cells = cal_panel.find_elements(By.CSS_SELECTOR, "button.mat-calendar-body-cell")

    for btn in cells:
        aria = btn.get_attribute("aria-label").strip()
        if aria in candidates:
            btn.click()
            return

    seen = [btn.get_attribute("aria-label").strip() for btn in cells]
    print("Versuchte Labels:", candidates)
    print("Gefundene: ", seen)
    raise RuntimeError("Code geht nicht")


def get_current_year_month(cal_panel):
    header_locator = (By.CSS_SELECTOR, ".mat-calendar-period-button")
    raw = cal_panel.find_element(*header_locator).text.strip().upper().rstrip(".")
    month_str, year_str = raw.split()
    month = GERMAN_FULL_UPPER[month_str]
    year = int(year_str)
    return year, month


def select_date_range(driver, start: date, end: date):
    wait = WebDriverWait(driver, 15)

    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "button.canvas-date-input")
    )).click()

    calendars = wait.until(EC.visibility_of_all_elements_located(
        (By.CSS_SELECTOR, ".mat-calendar")
    ))
    start_cal, end_cal = calendars

    def click_until(previous_or_next: str, cal_panel, target_header):
        prev_or_next_btn = cal_panel.find_element(
            By.CSS_SELECTOR, f"button.mat-calendar-{previous_or_next}-button"
        )
        header_selector = (By.CSS_SELECTOR, ".mat-calendar-period-button")

        for _ in range(48):
            header_text = cal_panel.find_element(*header_selector).text.strip().upper()
            if header_text == target_header:
                return
            prev_or_next_btn.click()
            wait.until(lambda d:
                cal_panel.find_element(*header_selector).text.strip().upper() != header_text
            )
        raise RuntimeError(f"Could not navigate to month '{target_header}'")

    start_header = f"{GERMAN_MONTHS[start.month]} {start.year}"
    end_header   = f"{GERMAN_MONTHS[end.month]} {end.year}"

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

    click_day_button(start_cal, start, wait)
    click_day_button(end_cal, end, wait)

    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "button.apply-button")
    )).click()


# Bestehende Funktionen (nicht verändert)
def scrape_website(website):
    print("Launching Chrome Browser.....")

    chrome_driver_path = "../chromedriver.exe"
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
    driver.maximize_window()

    try:
        driver.get(website)
        print("Website loaded.....")
        print("Bitte im geöffneten Chrome-Fenster mit Google-Account einloggen und das Dashboard komplett laden!")
        input("Drücke [Enter], sobald du eingeloggt bist und das Dashboard angezeigt wird ...")
        return driver  # gibt den geöffneten Driver zurück, damit du z. B. select_date_range aufrufen kannst
    except Exception as e:
        driver.quit()
        raise e


def extract_body_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    body_content = soup.body
    if body_content:
        return str(body_content)
    return ""


def clean_body_content(body_content):
    soup = BeautifulSoup(body_content, "html.parser")

    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()

    cleaned_content = soup.get_text(separator="\n")
    cleaned_content = "\n".join(
        line.strip() for line in cleaned_content.splitlines() if line.strip()
    )

    return cleaned_content


def split_dom_content(dom_content, max_length=6000):
    return [
        dom_content[i: i + max_length] for i in range(0, len(dom_content), max_length)
    ]
