import pandas as pd

df = pd.read_excel('Current Consumption.xlsx')
print(df.columns.tolist())
print(df.head())
