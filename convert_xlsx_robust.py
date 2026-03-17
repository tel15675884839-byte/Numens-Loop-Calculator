import pandas as pd
import json
import os

file_path = r"d:\Users\30741\Desktop\Loop Calculater\Current Consumption.xlsx"
df = pd.read_excel(file_path)

# 打印列名以便检查
print(f"Columns found: {df.columns.tolist()}")

# 尝试匹配列
# 期望列: Device Name, Standby(uA) 或 Standby(mA), Alarm(mA), LED Cost, Type
# 我们需要将其转换为 devices.json 的格式:
# {"name": "...", "standby": 0.26, "alarm": 5.0, "ledCost": 1, "type": "Detector"}

results = []
for _, row in df.iterrows():
    device = {
        "name": str(row.get('Device Name', row.iloc[0])),
        "standby": float(row.get('Standby(mA)', row.get('Standby', row.iloc[1]))),
        "alarm": float(row.get('Alarm(mA)', row.get('Alarm', row.iloc[2]))),
        "ledCost": int(row.get('LED Cost', row.get('LED', 1) if len(row) > 3 else 1)),
        "type": str(row.get('Type', 'Detector'))
    }
    # 如果 standby 是 uA，转换为 mA
    if 'Standby(uA)' in df.columns:
        device["standby"] = float(row['Standby(uA)']) / 1000.0
    
    results.append(device)

output_path = r"d:\Users\30741\Desktop\Loop Calculater\devices_new.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print(f"Successfully converted to {output_path}")
