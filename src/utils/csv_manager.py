import csv
import os
from typing import List, Dict, Union


class CSVFileHandler:
    def __init__(self, file_path: str, headers=None):
        self.file_path = file_path
        self.headers = headers

        # If headers are provided, check whether to write them
        if headers:
            file_missing = not os.path.exists(file_path)  # Check if file exists
            file_empty = file_missing or os.path.getsize(file_path) == 0  # Check if file is empty
            if file_empty:
                # Create file and write headers if file is missing or empty
                with open(self.file_path, mode='w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
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

    def append_row(self, row: Union[List, Dict], check_duplicate=True):
        """
        Append a row to the CSV file. If check_duplicate is True, skip row if it already exists.
        Ensures that the file ends with a newline before appending.
        """
        # Ensure the file ends with a newline character to prevent merging with the last row
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, mode='rb+') as f:
                    f.seek(-1, os.SEEK_END)  # Move to the last byte of the file
                    last_char = f.read(1)
                    if last_char not in (b'\n', b'\r'):
                        f.write(b'\n')  # Add newline if not present
            except OSError:
                # File might be empty or too small to seek; ignore
                pass

        if check_duplicate and self.row_exists(row):
            return  # Skip duplicate

        # Append row in appropriate format (dict or list)
        if isinstance(row, dict):
            if not self.headers:
                raise ValueError("Ohne header kannst du keine Dictionary nutzen.")
            with open(self.file_path, mode='a', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=self.headers)
                writer.writerow(row)
        else:
            with open(self.file_path, mode='a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(row)
