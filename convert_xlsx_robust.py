import pandas as pd
import json
import os

file_path = r"d:\Users\30741\Desktop\Loop Calculator\Current Consumption.xlsx"
df = pd.read_excel(file_path)

# ... (omitted code)

output_path = r"d:\Users\30741\Desktop\Loop Calculator\devices_new.json"with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print(f"Successfully converted to {output_path}")
