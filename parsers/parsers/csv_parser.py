import requests
import pandas as pd

from .base_parser import BaseParser

ALLOWED_EXTENSIONS = {"csv", "xls", "xlsx"}
CATEGORY_API_URL = "https://api.graintrade.info/categories"


class CSVParser(BaseParser):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_ext = file_path.split(".")[-1].lower()
        if self.file_ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file extension: {self.file_ext}")

    def parse(self) -> list[dict]:
        if self.file_ext == "csv":
            return parse_csv(self.file_path)
        elif self.file_ext in {"xls", "xlsx"}:
            return parse_excel(self.file_path)
        else:
            raise ValueError(f"Unsupported file extension: {self.file_ext}")

    def save_results(
        self, results: list[dict], filepath: str, file_ext: str = "csv"
    ) -> None:
        if file_ext != "csv":
            raise ValueError("Currently only 'csv' format is supported for saving.")
        save_to_csv(results, filepath)


def parse_csv(file_path: str):
    df = pd.read_csv(file_path)
    return df.to_dict(orient="records")


def save_to_csv(data: list, file_path: str):
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)


def parse_excel(file_path: str):
    ext = file_path.split(".")[-1].lower()
    if ext == "xls":
        # xlrd supports legacy .xls files
        df = pd.read_excel(file_path, engine="xlrd")
    else:
        # openpyxl for .xlsx
        df = pd.read_excel(file_path, engine="openpyxl")
    return df.to_dict(orient="records")


def fetch_categories() -> dict:
    response = requests.get(CATEGORY_API_URL)
    response.raise_for_status()
    categories = response.json()
    return categories


def parse_categories_to_excel(categories: dict, file_path: str) -> None:
    records = []

    def _traverse(cat_list):
        for cat in cat_list:
            records.append(
                {
                    "id": cat["id"],
                    "name": cat["name"],
                    "ua_name": cat["ua_name"],
                    "description": cat.get("description", ""),
                    "ua_description": cat.get("ua_description", ""),
                    "parent_category": cat["parent_category"],
                    "parent_category_ua": cat["parent_category_ua"],
                }
            )

    _traverse(categories)
    df = pd.DataFrame(records)
    df.to_excel(file_path, index=False)


if __name__ == "__main__":
    sample_data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    save_to_csv(sample_data, "output.csv")
    parsed_data = parse_csv("output.csv")
    print(parsed_data)
