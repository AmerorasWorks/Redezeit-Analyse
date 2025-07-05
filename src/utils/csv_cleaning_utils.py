import os
import re

def prepare_data_paths(base_dir=None):
    if base_dir is None:
        base_dir = os.getcwd()

    # Konsistenter Pfad für die Rohdaten
    output_folder = os.path.normpath(os.path.join(base_dir, "src", "data", "raw"))

    # Pfad für bereinigte Daten
    clean_folder = os.path.normpath(os.path.join(base_dir, "src", "data", "clean"))
    os.makedirs(clean_folder, exist_ok=True)

    file_names = [
        "landingpage.csv",
        "user_behaviors.csv",
        "what_devices_used_chart.csv",
        "what_did_user_do.csv",
        "where_did_they_come_from.csv",
        "where_new_visitors_come_from_chart.csv",
        "who_was_visiting_chart.csv",
    ]

    final_names = {
        "landingpage.csv": "landing_page_views.csv",
        "user_behaviors.csv": "user_sessions.csv",
        "what_devices_used_chart.csv": "device_usage.csv",
        "what_did_user_do.csv": "user_events.csv",
        "where_did_they_come_from.csv": "traffic_sources.csv",
        "where_new_visitors_come_from_chart.csv": "traffic_source_chart.csv",
        "who_was_visiting_chart.csv": "daily_visitors_chart.csv",
    }

    expected_columns = {
        "landingpage.csv": 3,
        "user_behaviors.csv": 3,
        "what_devices_used_chart.csv": 4,
        "what_did_user_do.csv": 6,
        "where_did_they_come_from.csv": 3,
        "where_new_visitors_come_from_chart.csv": 6,
        "who_was_visiting_chart.csv": 6,
    }

    return {
        "output_folder": output_folder,
        "clean_folder": clean_folder,
        "file_names": file_names,
        "final_names": final_names,
        "expected_columns": expected_columns,
    }


def to_snake_case(col_name):
    col_name = col_name.strip().lower()
    col_name = re.sub(r"[^\w\s]", "", col_name)  # Remove special chars
    col_name = re.sub(r"\s+", "_", col_name)  # Replace whitespace with _
    return col_name


def validate_csv(file_path, expected_cols):
    problems = []
    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if line.strip() and len(line.split(",")) != expected_cols:
                problems.append((i, line.strip()))
    return problems


def copy_and_validate_csvs(
    paths: dict, log=None, show_log=None, log_container=None
):
    output_folder = paths["output_folder"]
    clean_folder = paths["clean_folder"]
    file_names = paths["file_names"]
    final_names = paths["final_names"]
    expected_columns = paths["expected_columns"]

    cleaned_files = []

    for raw_fname in file_names:
        raw_path = os.path.join(output_folder, raw_fname)
        final_name = final_names.get(raw_fname, raw_fname)
        clean_path = os.path.join(clean_folder, final_name)

        if not os.path.exists(raw_path):
            continue

        os.makedirs(clean_folder, exist_ok=True)

        try:
            with open(raw_path, "r", encoding="utf-8") as infile:
                raw_lines = infile.readlines()

            if not raw_lines:
                continue  # Leere Datei überspringen

            # Header-Zeile formatieren
            header = raw_lines[0].strip().split(";")
            header_snake = [to_snake_case(col) for col in header]
            clean_lines = [";".join(header_snake) + "\n"] + raw_lines[1:]

            with open(clean_path, "w", encoding="utf-8") as outfile:
                outfile.writelines(clean_lines)

            # Optional: CSV-Validierung
            problems = validate_csv(
                clean_path, expected_columns.get(raw_fname, len(header_snake))
            )
            if problems:
                pass
            else:
                cleaned_files.append(clean_path)

        except Exception as e:
            pass

    # Abschließende Log-Meldung
    if not cleaned_files:
        pass
    else:
        log("✅ Alle Daten wurden in den clean-Ordner geschrieben.", "success")

    if log_container:
        show_log(log_container)
