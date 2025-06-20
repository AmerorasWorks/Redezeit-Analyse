import os
import csv
import random
from datetime import datetime, timedelta

# ── Helper to prevent overwrites & add "dummy_" prefix ─────────────────────────
def unique_filepath(folder: str, original_filename: str, prefix: str = "dummy_") -> str:
    base, ext = os.path.splitext(original_filename)
    candidate = f"{prefix}{base}{ext}"
    count = 1
    while os.path.exists(os.path.join(folder, candidate)):
        candidate = f"{prefix}{base}_{count}{ext}"
        count += 1
    return os.path.join(folder, candidate)

# ── Define where to write files ───────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(__file__)
BASE_FOLDER = os.path.join(SCRIPT_DIR, "Dummy_Data")
FACT_FOLDER = os.path.join(BASE_FOLDER, "Dummy_Fact")
DIM_FOLDER  = os.path.join(BASE_FOLDER, "Dummy_Dim")

# Ensure all folders exist
os.makedirs(FACT_FOLDER, exist_ok=True)
os.makedirs(DIM_FOLDER, exist_ok=True)

# ── Utility: last N days as list of date strings ──────────────────────────────
def get_date_list(days=30):
    today = datetime.today()
    return [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)][::-1]

dates = get_date_list(30)

# ── Master dimension values ───────────────────────────────────────────────────
continents = ["America", "Europe", "Asia", "Africa", "Oceania"]
countries  = ["United States", "Germany", "India", "Nigeria", "Australia"]
regions    = ["California", "Bavaria", "Maharashtra", "Abuja", "New South Wales"]
channels   = ["Organic Search", "Paid Search", "Referral", "Social", "Email"]
devices    = ["Desktop", "Mobile", "Tablet"]

# For dim_page: title + category pairs
page_dims = [
    ("Home", "Landing"),
    ("Product A", "Product"),
    ("Blog Post 1", "Blog"),
    ("Contact Us", "Support"),
    ("Pricing", "Sales")]
# For wide fact: just titles
pages = [title for title, _ in page_dims]

sources = ["google.com", "bing.com", "facebook.com", "newsletter"]
genders = ["Male", "Female", "Other"]
events  = ["click", "scroll", "video_play"]

# ── Write dimension tables ────────────────────────────────────────────────────
# dim_date
with open(unique_filepath(DIM_FOLDER, "dim_date.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Date", "Year", "Month", "Weekday"])
    for d in dates:
        dt = datetime.strptime(d, "%Y-%m-%d")
        w.writerow([d, dt.year, dt.month, dt.strftime("%A")])

# dim_continent
with open(unique_filepath(DIM_FOLDER, "dim_continent.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Continent"])
    for c in continents:
        w.writerow([c])

# dim_country
with open(unique_filepath(DIM_FOLDER, "dim_country.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Country"])
    for c in countries:
        w.writerow([c])

# dim_region
with open(unique_filepath(DIM_FOLDER, "dim_region.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Region"])
    for r in regions:
        w.writerow([r])

# dim_channel
with open(unique_filepath(DIM_FOLDER, "dim_channel.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Channel"])
    for ch in channels:
        w.writerow([ch])

# dim_device
with open(unique_filepath(DIM_FOLDER, "dim_device.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Device"])
    for d in devices:
        w.writerow([d])

# dim_page
with open(unique_filepath(DIM_FOLDER, "dim_page.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["PageTitle", "PageCategory"])
    for title, cat in page_dims:
        w.writerow([title, cat])

# dim_source
with open(unique_filepath(DIM_FOLDER, "dim_source.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Source"])
    for s in sources:
        w.writerow([s])

# dim_gender
with open(unique_filepath(DIM_FOLDER, "dim_gender.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Gender"])
    for g in genders:
        w.writerow([g])

# dim_event_name
with open(unique_filepath(DIM_FOLDER, "dim_event_name.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["EventName"])
    for e in events:
        w.writerow([e])

# ── Write fact tables in wide format ───────────────────────────────────────────
# fact_summary
with open(unique_filepath(FACT_FOLDER, "fact_summary.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Date", "PageViews", "TotalUsers", "AvgTimeOnSite", "BounceRate", "PagesPerSession"])
    for d in dates:
        w.writerow([
            d,
            random.randint(1000, 5000),
            random.randint(800, 4500),
            round(random.uniform(30, 300), 2),
            round(random.uniform(20, 70), 2),
            round(random.uniform(1.5, 5.0), 2)
        ])

# fact_landing_page
with open(unique_filepath(FACT_FOLDER, "fact_landing_page.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Date"] + pages)
    for d in dates:
        visits = [random.randint(100, 1000) for _ in pages]
        w.writerow([d] + visits)

# fact_visit_source
with open(unique_filepath(FACT_FOLDER, "fact_visit_source.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    header = ["Date"] + [f"{s}_Visits" for s in sources]
    w.writerow(header)
    for d in dates:
        w.writerow([d] + [random.randint(50, 500) for _ in sources])

# fact_device_breakdown
with open(unique_filepath(FACT_FOLDER, "fact_device_breakdown.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Date"] + devices)
    for d in dates:
        visits = [random.randint(200, 2000) for _ in devices]
        w.writerow([d] + visits)

# fact_origin_breakdown
with open(unique_filepath(FACT_FOLDER, "fact_origin_breakdown.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Date"] + sources)
    for d in dates:
        w.writerow([d] + [random.randint(50, 800) for _ in sources])

# fact_gender_distribution
with open(unique_filepath(FACT_FOLDER, "fact_gender_distribution.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Date"] + genders)
    for d in dates:
        w.writerow([d] + [random.randint(100, 1000) for _ in genders])

# fact_geo_data: Visits per region
with open(unique_filepath(FACT_FOLDER, "fact_geo_data.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Date"] + regions)
    for d in dates:
        w.writerow([d] + [random.randint(0, 500) for _ in regions])

# fact_interaction
with open(unique_filepath(FACT_FOLDER, "fact_interaction.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    header = ["Date"] + [f"{e}_ActiveUsers" for e in events] + [f"{e}_EventCount" for e in events]
    w.writerow(header)
    for d in dates:
        row = [d]
        for _ in events:
            active = random.randint(10, 200)
            count  = random.randint(active, active * 5)
            row += [active, count]
        w.writerow(row)

print("All dummy tables written in wide mode to Dummy_Fact/ and Dummy_Dim/")
