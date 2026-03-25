"""Test data files initialization"""

import json
from pathlib import Path

# Create data directory if it doesn't exist
data_dir = Path(__file__).parent.parent / "data"
data_dir.mkdir(exist_ok=True)

# Sample crops
crops = [
    "Wheat", "Corn", "Barley", "Rye", "Oats", "Millet",
    "Soybean", "Pea", "Chickpea", "Lentil", "Bean",
    "Sunflower", "Rapeseed", "Safflower", "Sesame",
    "Seed Wheat", "Seed Barley", "Seed Sunflower",
    "Urea", "Ammonia Nitrate", "DAP", "MAP", "Potassium Chloride",
    "Flour", "Meal", "Hay", "Straw", "Sugar Beet", "Rice", "Buckwheat"
]

# Sample ports
ports = [
    "Izmail", "Reni", "Kilia",
    "Odesa", "Chornomorsk", "Pivdennyy",
    "Brest", "Minsk",
    "Samsun", "Rize", "Trabzon",
    "Constanta", "Galati",
    "Varna", "Burgas",
    "Alexandria", "Port Said", "Suez",
]

# Sample regions
regions = [
    "Kyiv", "Kharkiv", "Odesa", "Dnipropetrovsk", "Donetsk", "Luhansk",
    "Zaporizhzhia", "Kherson", "Mykolaiv", "Cherkasy", "Poltava",
    "Chernihiv", "Sumy", "Zhytomyr", "Vinnytsia", "Khmelnytskyi",
    "Ternopil", "Ivano-Frankivsk", "Lviv", "Volyn",
    "Shpola", "Cherkaska",
    "Poland", "Moldova", "Romania", "Hungary", "Slovakia", "Belarus", "Russia",
]

# Delivery terms
delivery_terms = [
    "FOB", "CIF", "DDP", "EXW", "FAS", "CFR", "CPT", "DAP", "DAT", "FCA"
]

# Currencies
currencies = [
    "USD", "EUR", "UAH", "GBP", "CAD", "AUD", "CHF",
    "CNY", "JPY", "INR", "BRL", "RUB", "TRY", "PLN",
]

# Write JSON files
for name, data in [
    ("crops.json", crops),
    ("ports.json", ports),
    ("regions.json", regions),
    ("delivery_terms.json", delivery_terms),
    ("currencies.json", currencies),
]:
    file_path = data_dir / name
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Created {file_path}")
