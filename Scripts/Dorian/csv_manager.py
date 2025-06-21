import csv
import os
from typing import List, Dict, Union, Optional


class CSVFileHandler:
    def __init__(self, file_path: str, headers: Optional[List[str]] = None):
        self.file_path = file_path
        self.headers = headers

        if headers:
            write_header = False
        if not os.path.exists(file_path):
            write_header = True
        else:
            if os.path.getsize(file_path) == 0:
                write_header = True

        if write_header:
            with open(self.file_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)

    def append_row(self, row: Union[List, Dict]):
        if isinstance(row, dict):
            if not self.headers:
                raise ValueError("Ohne header kannst du keine Dictionary nutzen.")
            with open(self.file_path, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.headers)
                writer.writerow(row)
        else:
            with open(self.file_path, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
