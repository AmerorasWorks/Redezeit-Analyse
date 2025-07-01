import csv
import os
from typing import List, Dict, Union

class CSVFileHandler:
    def __init__(self, file_path: str, headers=None):
        self.file_path = file_path
        self.headers = headers

        # Only write header if file does not exist or is empty
        if headers:
            file_missing = not os.path.exists(file_path)
            file_empty = file_missing or os.path.getsize(file_path) == 0
            if file_empty:
                with open(self.file_path, mode='w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(self.headers)

    def row_exists(self, row: Union[List, Dict]) -> bool:
        if not os.path.exists(self.file_path):
            return False

        with open(self.file_path, newline='', encoding='utf-8-sig') as f:
            if self.headers:
                reader = csv.DictReader(f)
                for existing_row in reader:
                    if isinstance(row, dict):
                        if all(str(row[h]) == existing_row[h] for h in self.headers):
                            return True
                    else:
                        # comparing list to dict values; fallback no match
                        pass
            else:
                reader = csv.reader(f)
                for existing_row in reader:
                    if row == existing_row:
                        return True
        return False

    def append_row(self, row: Union[List, Dict], check_duplicate=True):
        if check_duplicate and self.row_exists(row):
            return  # Skip duplicate

        if isinstance(row, dict):
            if not self.headers:
                raise ValueError("Ohne header kannst du keine Dictionary nutzen.")
            with open(self.file_path, mode='a', newline='', encoding='utf-8-sig') as f:
