import csv
import os
from typing import List, Dict, Union


class CSVFileHandler:
    def __init__(self,
                 file_path: str,
                 headers: List[str] = None,
                 delimiter: str = ';'):
        """
        file_path  — where to write
        headers    — optional list of column names (writes header if file empty)
        delimiter  — character to separate fields on write (default ';')
        """
        self.file_path = file_path
        self.headers   = headers
        self.delimiter = delimiter

        # Only write headers if file is missing or zero‐length
        file_missing = not os.path.exists(file_path)
        file_empty   = file_missing or os.path.getsize(file_path) == 0
        if headers and file_empty:
            with open(file_path, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=self.delimiter)
                writer.writerow(self.headers)

    def row_exists(self, row: Union[List, Dict]) -> bool:
        """
        Check if a given row already exists in the file.
        Prevents duplicate entries.
        """
        if not os.path.exists(self.file_path):
            return False

        with open(self.file_path, newline='', encoding='utf-8-sig') as f:
            if self.headers:
                # If headers exist, read as dictionary
                reader = csv.DictReader(f)
                for existing_row in reader:
                    if isinstance(row, dict):
                        # Compare values by header keys
                        if all(str(row[h]) == existing_row.get(h, '') for h in self.headers):
                            return True
            else:
                # No headers: compare as lists
                reader = csv.reader(f)
                for existing_row in reader:
                    if row == existing_row:
                        return True
        return False

    def append_row(self, row: Union[List, Dict], check_duplicate: bool = True):
        """
        Append a row to the CSV file.
        - Ensures the file ends with a newline before appending.
        - Optionally skips if row already exists.
        - Writes fields using self.delimiter (semicolon).
        """
        # 1) Skip duplicate if asked
        if check_duplicate and self.row_exists(row):
            return

        # 2) Ensure the file ends with a newline
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, mode='rb+') as f:
                    f.seek(-1, os.SEEK_END)
                    last_char = f.read(1)
                    if last_char not in (b'\n', b'\r'):
                        f.write(b'\n')
            except OSError:
                pass

        # 3) Append the row
        with open(self.file_path, mode='a', newline='', encoding='utf-8-sig') as f:
            if isinstance(row, dict):
                if not self.headers:
                    raise ValueError("Ohne header kannst du keine Dictionary nutzen.")
                writer = csv.DictWriter(
                    f,
                    fieldnames=self.headers,
                    delimiter=self.delimiter
                )
            else:
                writer = csv.writer(f, delimiter=self.delimiter)

            writer.writerow(row)
