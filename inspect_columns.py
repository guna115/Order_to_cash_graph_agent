import pandas as pd
import glob

files = glob.glob("data/outbound_delivery_headers/*.jsonl")
if not files:
    print("No files found")
    raise SystemExit

df = pd.read_json(files[0], lines=True)
print("Columns:")
for c in df.columns:
    print("-", c)
print("\nSample row:")
print(df.head(1).to_dict(orient="records")[0])