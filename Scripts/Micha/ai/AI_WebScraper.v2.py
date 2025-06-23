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

EXPORT_DIR = "../exported_data"


def save_result_to_csv(result_text, export_dir=EXPORT_DIR):
    """
    Speichert das übergebene Parsing-Ergebnis als CSV-Datei im angegebenen Verzeichnis.
    Jede Zeile des Ergebnisses wird als Eintrag in einer Spalte gespeichert.
    Gibt den Pfad zur gespeicherten Datei zurück.
    """
    # Ordner anlegen, falls nicht vorhanden
    os.makedirs(export_dir, exist_ok=True)
    # Zeitstempel für eindeutigen Dateinamen
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    file_path = os.path.join(export_dir, f"parsed_result_{timestamp}.csv")
    # Zeilenweise speichern
    rows = [line for line in result_text.split("\n") if line.strip()]
    df = pd.DataFrame(rows, columns=["Result"])
    df.to_csv(file_path, index=False, encoding="utf-8")
    return file_path


def main():
    st.title("AI Web Scraper")
    url = st.text_input("Enter a Website URL:")

    # Datumsauswahl im Streamlit-UI
    start_date = st.date_input("Startdate", date.today() - timedelta(days=7))
    end_date = st.date_input("Enddate", date.today() - timedelta(days=1))

    if st.button("Scrape Site!"):
        st.write("Launching browser and loading site...")
        driver = scrape_website(url)

        # Erstelle Liste aller Tage im Zeitraum
        alle_tage = []
        aktuelles_datum = start_date
        while aktuelles_datum <= end_date:
            alle_tage.append(aktuelles_datum)
            aktuelles_datum += timedelta(days=1)

        gesamter_inhalt = ""

        # Für jeden Tag das Datum einzeln setzen, laden, auslesen
        for tag in alle_tage:
            st.write(f"Setze Datum auf: {tag}")
            select_date_range(driver, tag, tag)  # Zeitraum je ein Tag
            st.write("Warte 10 Sekunden, bis Kalender geladen ist...")
            time.sleep(10)
            html = driver.page_source

            body_content = extract_body_content(html)
            cleaned_content = clean_body_content(body_content)
            gesamter_inhalt += f"\n\n=== Inhalt für {tag} ===\n{cleaned_content}"

        driver.quit()

        st.session_state.dom_content = gesamter_inhalt

        with st.expander("View DOM Content"):
            st.text_area("DOM Content", gesamter_inhalt, height=300)

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
