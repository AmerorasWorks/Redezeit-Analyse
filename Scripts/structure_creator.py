import os
import csv

# Base data folder (adjusted to be at the same level as the script)
BASE_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Data", "Clean Data"))

# Fact and dimension subfolders
FACT_FOLDER = os.path.join(BASE_FOLDER, "Fact")
DIM_FOLDER = os.path.join(BASE_FOLDER, "Dim")

# Create directories if they don’t exist
os.makedirs(FACT_FOLDER, exist_ok=True)
os.makedirs(DIM_FOLDER, exist_ok=True)

# Define fact and dimension table schemas
fact_tables = {
    "fact_summary.csv": [
        "Date", "PageViews", "TotalUsers", "AvgTimeOnSite", "BounceRate", "PagesPerSession"
    ],
    "fact_landing_page.csv": [
        "Date", "PageTitle", "Visits"
    ],
    "fact_visit_source.csv": [
        "Date", "Source", "Clicks", "Calls", "CallsPerSession"
    ],
    "fact_device_breakdown.csv": [
        "Date", "Device", "Visits"
    ],
    "fact_origin_breakdown.csv": [
        "Date", "Source", "Visits"
    ],
    "fact_gender_distribution.csv": [
        "Date", "Gender", "Visits"
    ],
    "fact_geo_data.csv": [
        "Date", "Continent", "Country", "Region"
    ],
    "fact_interaction.csv": [
        "Date", "EventName", "EventLabel", "ActiveUsers", "EventCount"
    ]
}

dim_tables = {
    "dim_date.csv": ["Date", "Year", "Month", "Weekday"],
    "dim_continent.csv": ["Continent"],
    "dim_country.csv": ["Country"],
    "dim_region.csv": ["Region"],
    "dim_channel.csv": ["Channel"],
    "dim_device.csv": ["Device"],
    "dim_page.csv": ["PageTitle", "PageCategory"],
    "dim_source.csv": ["Source", "SourceType", "Link"],
    "dim_gender.csv": ["Gender"],
    "dim_event_name.csv": ["EventName", "Description"],
    "dim_event_label.csv": ["EventLabel", "UIElement"]
}

# Write fact tables
for filename, headers in fact_tables.items():
    filepath = os.path.join(FACT_FOLDER, filename)
    with open(filepath, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)

# Write dimension tables
for filename, headers in dim_tables.items():
    filepath = os.path.join(DIM_FOLDER, filename)
    with open(filepath, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)

print(f"CSV tables created in:\n- Fact: '{FACT_FOLDER}'\n- Dimension: '{DIM_FOLDER}'")
