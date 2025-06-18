import streamlit as st
from datetime import date, timedelta
from scrape_nardo import (
    scrape_website, split_dom_content, clean_body_content, extract_body_content, select_date_range
)
from parse_nardo import parse_with_ollama
import time
import os
import pandas as pd

EXPORT_DIR = "exported_data"

def save_result_to_csv(result_text, export_dir=EXPORT_DIR, datum=None):
    """
    Speichert Parsing-Ergebnis als CSV, Dateiname enthält Datum.
    """
    os.makedirs(export_dir, exist_ok=True)
    if datum:
        fname = f"parsed_result_{datum}.csv"
    else:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        fname = f"parsed_result_{timestamp}.csv"
    file_path = os.path.join(export_dir, fname)
    rows = [line for line in result_text.split("\n") if line.strip()]
    df = pd.DataFrame(rows, columns=["Result"])
    df.to_csv(file_path, index=False, encoding="utf-8")
    return file_path

def automatic_google_login(driver, email, password):
    """
    Automatischer Login bei Google im geöffneten Chrome-Fenster.
    """
    driver.get("https://accounts.google.com/signin")
    time.sleep(2)
    email_field = driver.find_element("ID", "identifierId")
    email_field.send_keys(email)
    driver.find_element("ID", "identifierNext").click()
    time.sleep(2)
    pass_field = driver.find_element("NAME", "password")
    pass_field.send_keys(password)
    driver.find_element("ID", "passwordNext").click()
    time.sleep(5)

def daterange(start_date, end_date):
    """
    Generator für jeden Tag im Zeitraum.
    """
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def main():
    st.title("AI Web Scraper: ")
    url = st.text_input("Website URL")
    # email = st.text_input("Google E-Mail")
    # password = st.text_input("Google Password", type="password")

    start_date = st.date_input("Startdate", date.today() - timedelta(days=7))
    end_date = st.date_input("Enddate", date.today() - timedelta(days=1))
    parse_description = st.text_area("Describe what Content you want to parse? (Prompt)")

    if st.button("Start Scraping each Day"):
        st.write("Start Auto-Login & Day wise Scraping...")
        driver = scrape_website(url)  # Dashboard-URL laden
        automatic_google_login(driver, email, password)  # Automatischer Login

        for current_day in daterange(start_date, end_date):
            st.write(f"Scraping {current_day.strftime('%d.%m.%Y')} in progress...")
            # Automatische Datums-Auswahl (jeweils einen Tag als Range setzen)
            select_date_range(driver, current_day, current_day)
            time.sleep(15)  # Warte bis Daten laden

            html = driver.page_source
            body_content = extract_body_content(html)
            cleaned_content = clean_body_content(body_content)
            dom_chunks = split_dom_content(cleaned_content)

            # Parsing
            result = parse_with_ollama(dom_chunks, parse_description)

            # Speichern
            date_str = current_day.strftime("%Y-%m-%d")
            file_path = save_result_to_csv(result, datum=date_str)
            st.success(f"Saved: {file_path}")

        driver.quit()
        st.success("Day wise Scraping completed!")

if __name__ == "__main__":
    main()
