import pandas as pd

# Sample data for items
data = [
    {
        "name": "Wheat",
        "category": "Grains",
        "price": 200,
        "description": "High quality wheat",
    },
    {"name": "Corn", "category": "Grains", "price": 150, "description": "Fresh corn"},
    {
        "name": "Barley",
        "category": "Grains",
        "price": 180,
        "description": "Premium barley",
    },
]
df = pd.DataFrame(data)
df.to_excel(
    "/home/kostiantyn/projects/graintrade-info/parsers/results/sample_items.xlsx",
    index=False,
)
print("Sample .xlsx file created.")
