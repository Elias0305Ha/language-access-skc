from pathlib import Path
import pandas as pd

df = pd.read_csv(Path("data/raw/ospi_languages_2024_25.csv"), dtype=str)

print(df["OrganizationLevel"].value_counts(dropna=False))

d = df[df["OrganizationLevel"] == "District"]
print("\ndistrict rows:", len(d))

print("\nKing County districts:")
for n in sorted(d.loc[d["County"] == "King", "DistrictName"].dropna().unique()):
    print("  ", n)
