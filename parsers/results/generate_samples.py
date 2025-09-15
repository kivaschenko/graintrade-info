import csv
import xlwt

# Columns and sample rows
columns = ["name", "category", "price", "description"]
rows = [
    ["Wheat", "Grains", 200, "High quality wheat"],
    ["Corn", "Grains", 150, "Fresh corn"],
    ["Barley", "Grains", 180, "Premium barley"],
]

base = "/home/kostiantyn/projects/graintrade-info/parsers/results"
csv_path = f"{base}/sample_items.csv"
xls_path = f"{base}/sample_items.xls"
template_xls_path = f"{base}/items_template.xls"

# Write CSV
with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(columns)
    writer.writerows(rows)
print("Sample CSV created.")

# Write XLS using xlwt
wb = xlwt.Workbook()
ws = wb.add_sheet("items")
for col, header in enumerate(columns):
    ws.write(0, col, header)
for r, row in enumerate(rows, start=1):
    for c, val in enumerate(row):
        ws.write(r, c, val)
wb.save(xls_path)
print("Sample XLS created.")

# Write template XLS (headers only + 1 example row)
wb_t = xlwt.Workbook()
ws_t = wb_t.add_sheet("items")
for col, header in enumerate(columns):
    ws_t.write(0, col, header)
example = rows[0]
for c, val in enumerate(example):
    ws_t.write(1, c, val)
wb_t.save(template_xls_path)
print("Template XLS created.")
