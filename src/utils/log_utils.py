import os
import csv
import streamlit as st
from datetime import datetime

SCRAPE_LOG_PATH = os.path.join("src", "data", "log", "scrape_log.csv")

if "log_messages" not in st.session_state:
    st.session_state.log_messages = []

def log(message: str, level: str = "info") -> None:
    colors = {
        "info": "#ffffff",
        "warning": "#bf9f00",
        "error": "#ae0000",
        "success": "#6fff00",
    }
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    color = colors.get(level, "#ffffff")
    styled_message = f'<div style="color: {color}; font-family: monospace;">[{timestamp}] {message}</div>'
    st.session_state.log_messages.append(styled_message)

def show_log(container):
    container.markdown(
        f"""
        <div id="log-container">
        {"".join(st.session_state.log_messages)}
        </div>
        """,
        unsafe_allow_html=True,
    )

def is_date_scraped(scrape_date) -> bool:
    if not os.path.exists(SCRAPE_LOG_PATH):
        return False
    with open(SCRAPE_LOG_PATH, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if row and row[0] == scrape_date.isoformat():
                return True
    return False

def log_scraped_date(scrape_date) -> None:
    os.makedirs(os.path.dirname(SCRAPE_LOG_PATH), exist_ok=True)
    file_exists = os.path.exists(SCRAPE_LOG_PATH)
    with open(SCRAPE_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Datum"])
        writer.writerow([scrape_date.isoformat()])
