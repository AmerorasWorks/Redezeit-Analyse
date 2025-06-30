# backend/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import date, timedelta
import os
import time
import pickle

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

import sys

sys.path.append(os.path.dirname(__file__))

from src.utils.kalender_funktion import select_date_range
from src.utils.csv_manager import CSVFileHandler

from src.scraper.landingpage_scraper import (
    extract_table_data as extract_landingpage_data,
)
from src.scraper.user_behaviors_scraper import extract_user_behaviour
from src.scraper.what_did_users_do_scraper import (
    extract_table_data as extract_events_data,
)
from src.scraper.where_did_they_come_from_scraper import (
    extract_table_data as extract_sources_data,
)
from src.scraper.where_new_visitors_come_from_chart import (
    extract_table_for_piechart_gviz as extract_pie_sources,
)
from src.scraper.what_devices_used_chart import (
    extract_table_for_piechart_gviz as extract_pie_devices,
)
from src.scraper.who_was_visiting_chart import (
    extract_table_for_piechart_gviz as extract_pie_visitors,
)

app = FastAPI()

COOKIE_PATH = "src/cookies/cookies.pkl"
URL = "https://lookerstudio.google.com/u/0/reporting/3c1fa903-4f31-4e6f-9b54-f4c6597ffb74/page/4okDC"


class DateRange(BaseModel):
    start_date: date
    end_date: date


def init_driver_with_cookies():
    service = Service()
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(URL)

    if os.path.exists(COOKIE_PATH):
        with open(COOKIE_PATH, "rb") as f:
            cookies = pickle.load(f)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception:
                pass
        driver.refresh()
        time.sleep(5)
    else:
        raise HTTPException(
            status_code=400,
            detail="Cookies nicht gefunden, bitte zuerst login und Cookies speichern.",
        )

    return driver


def save_cookies(driver):
    cookies = driver.get_cookies()
    with open(COOKIE_PATH, "wb") as f:
        pickle.dump(cookies, f)


@app.post("/save-cookies")
def api_save_cookies():
    service = Service()
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(URL)
    return {
        "detail": "Bitte melde dich im Chrome-Fenster an und schließe es nach dem Login."
    }


@app.post("/run-scraper")
def api_run_scraper(dates: DateRange):
    start_date = dates.start_date
    end_date = dates.end_date

    driver = init_driver_with_cookies()
    output_folder = os.path.join("src/Data")
    os.makedirs(output_folder, exist_ok=True)

    current = start_date
    results = []
    while current <= end_date:
        try:
            select_date_range(driver, current, current)
            time.sleep(8)

            # Landingpage
            data = extract_landingpage_data(driver, current.isoformat())
            lp_csv = CSVFileHandler(
                os.path.join(output_folder, "landingpage.csv"),
                headers=["Datum", "EID", "Seitentitel", "Aufrufe"],
            )
            for row in data:
                lp_csv.append_row(row)

            # User Behaviour
            row = extract_user_behaviour(driver, current)
            if row:
                ub_csv = CSVFileHandler(
                    os.path.join(output_folder, "user_behaviors.csv"),
                    headers=[
                        "Datum",
                        "Seitenaufrufe",
                        "Nutzer Insgesamt",
                        "Durchschn. Zeit auf der Seite",
                        "Absprungrate",
                        "Seiten / Sitzung",
                    ],
                )
                ub_csv.append_row(row)

            # Events
            data = extract_events_data(driver, current.isoformat())
            ev_csv = CSVFileHandler(
                os.path.join(output_folder, "what_did_user_do.csv"),
                headers=[
                    "Datum",
                    "EID",
                    "Name des Events",
                    "even_label",
                    "Aktive Nutzer",
                    "Ereignisanzahl",
                ],
            )
            for row in data:
                ev_csv.append_row(row)

            # Quellen Tabelle
            data = extract_sources_data(driver, current.isoformat())
            src_csv = CSVFileHandler(
                os.path.join(output_folder, "where_did_they_come_from.csv"),
                headers=[
                    "Datum",
                    "EID",
                    "Quelle",
                    "Sitzungen",
                    "Aufrufe",
                    "Aufrufe pro Sitzung",
                ],
            )
            for row in data:
                src_csv.append_row(row)

            # Piecharts:
            for label, func in zip(
                [
                    "where_new_visitors_come_from_chart",
                    "what_devices_used_chart",
                    "who_was_visiting_chart",
                ],
                [extract_pie_sources, extract_pie_devices, extract_pie_visitors],
            ):
                pie_data = func(driver, current.isoformat())
                pie_csv = CSVFileHandler(
                    os.path.join(output_folder, f"{label}.csv"),
                    headers=["Datum", "Kategorie", "Wert"],
                )
                for row in pie_data:
                    pie_csv.append_row(row)

            results.append({"date": current.isoformat(), "status": "success"})
        except Exception as e:
            results.append(
                {"date": current.isoformat(), "status": "error", "message": str(e)}
            )

        current += timedelta(days=1)

    driver.quit()
    return {"detail": "Scraper fertig", "results": results}
