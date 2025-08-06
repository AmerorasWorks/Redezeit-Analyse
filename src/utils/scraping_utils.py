import os
import time
from datetime import timedelta
from src.utils.log_utils import log, show_log, is_date_scraped, log_scraped_date
from src.utils.chrome_utils import init_driver_with_cookies
from src.utils.calender_utils import select_date_range
from src.utils.csv_manager_utils import CSVFileHandler
from src.utils.csv_cleaning_utils import prepare_data_paths, copy_and_validate_csvs
from src.utils.file_utils import get_output_folder
from src.utils.scraper.landingpage_scraper import extract_table_data as extract_landingpage_data
from src.utils.scraper.user_behaviors_scraper import extract_user_behaviour
from src.utils.scraper.what_did_users_do_scraper import extract_table_data as extract_events_data
from src.utils.scraper.where_did_they_come_from_scraper import extract_table_data as extract_sources_data
from src.utils.scraper.where_new_visitors_come_from_chart import extract_table_for_piechart_gviz as extract_pie_sources
from src.utils.scraper.what_devices_used_chart import extract_table_for_piechart_gviz as extract_pie_devices
from src.utils.scraper.who_was_visiting_chart import extract_table_for_piechart_gviz as extract_pie_visitors



def run_all_scraper(start_date, end_date, log_container=None):
    output_folder = get_output_folder("raw")
    driver = init_driver_with_cookies()
    current = start_date
    new_data = False
    while current <= end_date:
        if is_date_scraped(current):
            log(f"📅 {current.isoformat()} Daten bereits extrahiert – gehe zum nächsten Datum.", "info")
            if log_container:
                show_log(log_container)
            current += timedelta(days=1)
            continue

        log(f"\n📆 Scraping für {current.isoformat()}", "info")
        if log_container:
            show_log(log_container)
        try:
            select_date_range(driver, current, current)
            time.sleep(8)

            data = extract_landingpage_data(driver, current.isoformat())
            lp_csv = CSVFileHandler(
                os.path.join(output_folder, f"landingpage.csv"),
                headers=["datum", "eid", "seitentitel", "aufrufe"],
            )
            for row in data:
                lp_csv.append_row(row)

            row = extract_user_behaviour(driver, current)
            if row:
                ub_csv = CSVFileHandler(
                    os.path.join(output_folder, f"user_behaviors.csv"),
                    headers=[
                        "datum",
                        "seitenaufrufe",
                        "nutzer insgesamt",
                        "durchschn. zeit auf der seite",
                        "absprungrate",
                        "seiten / sitzung",
                    ],
                )
                ub_csv.append_row(row)

            data = extract_events_data(driver, current.isoformat())
            ev_csv = CSVFileHandler(
                os.path.join(output_folder, f"what_did_user_do.csv"),
                headers=[
                    "datum",
                    "eid",
                    "name des events",
                    "event_label",
                    "aktive nutzer",
                    "ereignisanzahl",
                ],
            )
            for row in data:
                ev_csv.append_row(row)

            data = extract_sources_data(driver, current.isoformat())
            src_csv = CSVFileHandler(
                os.path.join(output_folder, f"where_did_they_come_from.csv"),
                headers=[
                    "datum",
                    "eid",
                    "quelle",
                    "sitzungen",
                    "aufrufe",
                    "aufrufe pro sitzung",
                ],
            )
            for row in data:
                src_csv.append_row(row)

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
                    headers=["datum", "kategorie", "wert"],
                )
                for row in pie_data:
                    pie_csv.append_row(row)

        except Exception as e:
            log(f"❌ Fehler am {current}: {e}", "error")
            if log_container:
                show_log(log_container)
        else:
            log_scraped_date(current)
            new_data = True
            log(f"✅ {current.isoformat()} geloggt.", "success")
            if log_container:
                show_log(log_container)
        finally:
            current += timedelta(days=1)

    driver.quit()
    time.sleep(5)

    paths = prepare_data_paths()
    raw_files_exist = any(
        os.path.exists(os.path.join(paths["output_folder"], fname))
        for fname in paths["file_names"]
    )
    if raw_files_exist and new_data:
        copy_and_validate_csvs(paths, log=log, show_log=show_log, log_container=log_container)
        log("✅ Alle CSV-Dateien wurden erfolgreich aufbereitet.", "success")
    else:
        log("⚠️ Keine Rohdaten gefunden!\nMöglicherweise ist beim Scraping ein Fehler aufgetreten!\nOder sind diese Daten bereits extrahiert worden? 🤔",
            "warning")
    if log_container:
        show_log(log_container)
