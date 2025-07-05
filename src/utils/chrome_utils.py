import os
import pickle
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from src.utils.file_utils import resource_path

def ensure_cookie_dir(folder_name: str = "cookies") -> Path:
    base_dir = os.path.abspath(".")
    cookie_dir = Path(base_dir) / folder_name
    cookie_dir.mkdir(exist_ok=True)
    return cookie_dir

COOKIE_DIR = ensure_cookie_dir()
COOKIE_PATH = COOKIE_DIR / "cookies.pkl"
URL = "https://lookerstudio.google.com/u/0/reporting/3c1fa903-4f31-4e6f-9b54-f4c6597ffb74/page/4okDC"

def get_chrome_driver() -> webdriver.Chrome:
    chrome_path = resource_path("chromedriver.exe")
    service = Service(executable_path=chrome_path)
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    return webdriver.Chrome(service=service, options=options)

def init_driver_with_cookies():
    import streamlit as st
    driver = get_chrome_driver()
    driver.get(URL)
    if COOKIE_PATH.exists():
        with open(COOKIE_PATH, "rb") as f:
            cookies = pickle.load(f)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                pass
        driver.refresh()
        time.sleep(5)
    else:
        st.warning("🔐 Bitte anmelden und dann erneut klicken.")
        st.stop()
    return driver

def save_cookies(driver):
    with open(COOKIE_PATH, "wb") as f:
        pickle.dump(driver.get_cookies(), f)
