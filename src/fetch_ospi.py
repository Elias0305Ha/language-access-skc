from pathlib import Path
import pandas as pd

URL = "https://data.wa.gov/api/v3/views/g4qj-yi5j/export.csv?accessType=DOWNLOAD"

Path("data/raw").mkdir(parents=True, exist_ok=True)
out = Path("data/raw/ospi_languages_2024_25.csv")

if not out.exists():
    pd.read_csv(URL, dtype=str).to_csv(out, index=False)
    print("downloaded")

df = pd.read_csv(out, dtype=str)

print(df.shape)
print(df.columns.tolist())
print(df.head(10).to_string())