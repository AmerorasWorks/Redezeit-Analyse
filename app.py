import streamlit as st
from datetime import date, timedelta
import time

from src.utils.file_utils import load_custom_css
from src.utils.chrome_utils import get_chrome_driver, save_cookies, URL
from src.utils.log_utils import log, show_log
from src.utils.scraping_utils import run_all_scraper

# CSS laden
load_custom_css("style.css")


def main():
    if "log_messages" not in st.session_state:
        st.session_state["log_messages"] = []
    st.markdown(
        """
        <style>header {visibility: hidden;}</style>
        <div class="custom-header"><div class="title"><h1>scrapetime</h1></div></div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<hr style='border:1px solid #ffffff;'>", unsafe_allow_html=True)
    st.subheader("Willkommen zum Redezeit-Scraping-Tool!")
    st.markdown(
        """
        <div class="custom-info">
            Hier kannst du Daten vom Redezeit-Dashboard extrahieren und in CSV-Dateien speichern.<br>
            Bitte beachte, dass du dich einmalig bei Google anmelden musst, um die Cookies zu speichern.<br>
            Danach kannst du die Scraper für einen bestimmten Zeitraum ausführen.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<hr style='border:1px solid #ffffff;'>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        start_date = st.date_input(
            "Startdatum", date.today() - timedelta(days=7), key="start"
        )
        end_date = st.date_input(
            "Enddatum", date.today() - timedelta(days=1), key="end"
        )

    with col2:
        st.markdown("### 📜 Log-Fenster")
        log_container = st.empty()

    with col1:
        if st.button("🔄 Einmaliger Login"):
            driver = get_chrome_driver()
            driver.get(URL)
            log(
                "🔐 Bitte im neuen Tab bei Google anmelden. Danach das Google-Tab schließen.",
                "info",
            )
            time.sleep(60)
            save_cookies(driver)
            driver.quit()
            log("✅ Cookies erfolgreich gespeichert.", "info")
            # show_log(log_container)

        if st.button("🚀 Scraper ausführen"):
            run_all_scraper(start_date, end_date, log_container)
            st.session_state["log_messages"].append(" ")

    show_log(log_container)
    log_html = '<div id="log-container">' + "<br>".join(st.session_state["log_messages"]) + '</div>'
    log_container.markdown(log_html, unsafe_allow_html=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback

        traceback.print_exc()
        input("Drücke Enter, um zu beenden…")
