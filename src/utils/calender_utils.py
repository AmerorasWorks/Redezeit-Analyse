from datetime import date
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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
