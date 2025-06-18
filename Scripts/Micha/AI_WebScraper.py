import streamlit as st
from datetime import date, timedelta
from scrape import (
    scrape_website,
    split_dom_content,
    clean_body_content,
    extract_body_content,
    select_date_range
)

from parse import parse_with_ollama
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


def main():
    st.title("AI Web Scraper with Calender & CSV Export")
    url = st.text_input("Enter a Website URL:")

    # Datumsauswahl im Streamlit-UI
    start_date = st.date_input("Startdate", date.today() - timedelta(days=7))
    end_date = st.date_input("Enddate", date.today() - timedelta(days=1))

    if st.button("Scrape Site!"):
        st.write("Launching browser and loading site...")
        driver = scrape_website(url)

        # Kalenderlogik ausführen
        st.write(f"Calender: {start_date} bis {end_date}")
        select_date_range(driver, start_date, end_date)
        st.write("Wait 15 seconds 'til Calender is loaded..")
        time.sleep(15)
        html = driver.page_source
        driver.quit()

        body_content = extract_body_content(html)
        cleaned_content = clean_body_content(body_content)
        st.session_state.dom_content = cleaned_content

        with st.expander("View DOM Content"):
            st.text_area("DOM Content", cleaned_content, height=300)

    # Optional: Inhalt analysieren und Ergebnis exportieren
    if "dom_content" in st.session_state:
        parse_description = st.text_area("Describe what Content you want to parse?")

        # Ergebnis zwischenspeichern
        if "parsed_result" not in st.session_state:
            st.session_state["parsed_result"] = None

        if st.button("Parse Content!"):
            if parse_description:
                st.write("Parsing the Content...")
                dom_chunks = split_dom_content(st.session_state.dom_content)
                result = parse_with_ollama(dom_chunks, parse_description)
                st.session_state["parsed_result"] = result
                st.write(result)

        # CSV-Export-Button erscheint nur bei vorhandenem Ergebnis
        if st.session_state.get("parsed_result"):
            if st.button("Export as CSV"):
                file_path = save_result_to_csv(st.session_state["parsed_result"])
                st.success(f"Saved CSV: {file_path}")

if __name__ == "__main__":
    main()
