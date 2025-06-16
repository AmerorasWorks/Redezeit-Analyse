from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
import easyocr
import time

options = Options()
options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(options=options)

url = "https://lookerstudio.google.com/u/0/reporting/3c1fa903-4f31-4e6f-9b54-f4c6597ffb74/page/4okDC"
driver.get(url)

time.sleep(10)

screenshot_path = "looker_report.png"
driver.save_screenshot(screenshot_path)

driver.quit()

reader = easyocr.Reader(['de', 'en'])
results = reader.readtext(screenshot_path)

for bbox, text, conf in results:
    print(f"{text} (Confidence: {conf:.2f})")
