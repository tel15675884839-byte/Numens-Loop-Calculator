import pandas as pd
import json

df = pd.read_excel('Current Consumption.xlsx')
results = []
for _, row in df.iterrows():
    device = {
        "name": str(row['name']),
        "standby": float(row['standby']),
        "alarm": float(row['alarm']),
        "ledCost": int(row['ledCost']),
        "type": str(row['type'])
    }
    results.append(device)

with open('devices_new.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print("Converted successfully")
