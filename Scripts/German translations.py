import os
import csv

# Base folders
BASE_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Data", "Clean Data"))
GERMAN_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Data", "Clean Data", "German Translation"))

FACT_FOLDER = os.path.join(BASE_FOLDER, "Fact")
DIM_FOLDER = os.path.join(BASE_FOLDER, "Dim")

GERMAN_FACT_FOLDER = os.path.join(GERMAN_FOLDER, "Fact")
GERMAN_DIM_FOLDER = os.path.join(GERMAN_FOLDER, "Dim")

os.makedirs(GERMAN_FACT_FOLDER, exist_ok=True)
os.makedirs(GERMAN_DIM_FOLDER, exist_ok=True)

# Translation dictionary
translation_dict = {
    # fact_summary.csv
    "Date": "Datum",
    "PageViews": "Seitenaufrufe",
    "TotalUsers": "Nutzer Insgesamt",
    "AvgTimeOnSite": "Ø Verweildauer",
    "BounceRate": "Absprungrate",
    "PagesPerSession": "Seiten/Sitzung",

    # fact_landing_page.csv
    "PageTitle": "Seitentitel",
    "Visits": "Besuche",

    # fact_visit_source.csv
    "Source": "Quelle",
    "Clicks": "Klicks",
    "Calls": "Anrufe",
    "CallsPerSession": "Anrufe pro Sitzung",

    # fact_device_breakdown.csv
    "Device": "Gerät",

    # fact_origin_breakdown.csv (same as visit_source)

    # fact_gender_distribution.csv
    "Gender": "Geschlecht",

    # fact_geo_data.csv
    "Continent": "Kontinent",
    "Country": "Land",
    "Region": "Region",

    # fact_interaction.csv
    "EventName": "Ereignisname",
    "EventLabel": "Ereignisbezeichnung",
    "ActiveUsers": "Aktive Nutzer",
    "EventCount": "Ereigniszähler",

    # dim_date.csv
    "Year": "Jahr",
    "Month": "Monat",
    "Weekday": "Wochentag",

    # dim_continent.csv
    # dim_country.csv
    # dim_region.csv

    # dim_channel.csv
    "Channel": "Kanal",
    # dim_device.csv

    # dim_page.csv
    "PageCategory": "Seitenkategorie",

    # dim_source.csv
    "SourceType": "Quellentyp",
    "Link": "Link",

    # dim_event_name.csv
    "Description": "Beschreibung",

    # dim_event_label.csv
    "UIElement": "UI-Element",
}

def translate_headers(headers):
    return [translation_dict.get(col, col) for col in headers]

def translate_csv(input_path, output_path):
    with open(input_path, mode='r', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        rows = list(reader)
        if not rows:
            print(f"Warning: '{input_path}' is empty.")
            return

        original_headers = rows[0]
        translated_headers = translate_headers(original_headers)

        # Write translated CSV
        with open(output_path, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(translated_headers)
            writer.writerows(rows[1:])

def translate_folder(input_folder, output_folder):
    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            translate_csv(input_path, output_path)

# Translate fact and dim folders
translate_folder(FACT_FOLDER, GERMAN_FACT_FOLDER)
translate_folder(DIM_FOLDER, GERMAN_DIM_FOLDER)

# Save translation dictionary as CSV for reference
dict_csv_path = os.path.join(GERMAN_FOLDER, "translation_dictionary.csv")
with open(dict_csv_path, mode='w', newline='', encoding='utf-8') as dict_file:
    writer = csv.writer(dict_file)
    writer.writerow(["English", "German"])
    for eng, ger in sorted(translation_dict.items()):
        writer.writerow([eng, ger])

print(f"Translated CSVs created in '{GERMAN_FOLDER}'.")
print(f"Translation dictionary saved as '{dict_csv_path}'.")
