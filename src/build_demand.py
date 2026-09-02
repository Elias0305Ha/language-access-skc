from pathlib import Path
import pandas as pd

DISTRICTS = [
    "Highline School District",
    "Tukwila School District",
    "Kent School District",
    "Federal Way School District",
    "Renton School District",
    "Auburn School District",
]

df = pd.read_csv(Path("data/raw/ospi_languages_2024_25.csv"), dtype=str)

d = df[(df["OrganizationLevel"] == "District")
       & (df["DistrictName"].isin(DISTRICTS))]

print("rows:", len(d))
print()
print(d["DistrictName"].value_counts())

col = "StudentCount_PreferredFamilyLanguage"
bad = d.loc[~d[col].fillna("").str.fullmatch(r"\d+"), col]
print("\nnon-numeric values in", col, ":", len(bad))
print(bad.value_counts().head())

d = d.copy()
d["preferred"] = d["StudentCount_PreferredFamilyLanguage"].astype(int)

non_english = d[d["LanguageName"] != "English"]

print("\nfamilies preferring English:", d.loc[d["LanguageName"] == "English", "preferred"].sum())
print("families preferring another language:", non_english["preferred"].sum())

top = (non_english.groupby("LanguageName")["preferred"]
       .sum().sort_values(ascending=False))

print("\ntop 20 non-English:")
print(top.head(20).to_string())


watch = ["Amharic", "Somali", "Oromo", "Tigrinya", "Chuukese",
         "Marshallese", "Punjabi", "Ukrainian", "Vietnamese", "Dari", "Pashto"]

print("\nyour watchlist:")
for lang in watch:
    hits = top[top.index.str.contains(lang, case=False, na=False)]
    if len(hits) == 0:
        print(f"  {lang}: NOT IN FILE")
    else:
        for name, val in hits.items():
            print(f"  {name}: {val}")


Path("data/processed").mkdir(parents=True, exist_ok=True)

top.to_csv("data/processed/languages_all.csv", header=["preferred_families"])
print("\nwrote", len(top), "languages to data/processed/languages_all.csv")
