import pandas as pd

DISTRICTS = [
    "Highline School District",
    "Tukwila School District",
    "Kent School District",
    "Federal Way School District",
    "Renton School District",
    "Auburn School District",
]

df = pd.read_csv("data/raw/ospi_languages_2024_25.csv", dtype=str)

d = df[(df["OrganizationLevel"] == "District")
       & (df["DistrictName"].isin(DISTRICTS))].copy()

d["preferred"] = d["StudentCount_PreferredFamilyLanguage"].astype(int)
d = d[d["LanguageName"] != "English"]

xw = pd.read_csv("data/reference/language_crosswalk.csv")
mapping = dict(zip(xw["source_name"], xw["canonical_name"]))

in_xw = d["LanguageName"].isin(mapping.keys())
d["canonical"] = d["LanguageName"].map(mapping)
d.loc[~in_xw, "canonical"] = d.loc[~in_xw, "LanguageName"]

resolved = d[d["canonical"].notna()]
unresolved = d[d["canonical"].isna()]

print("families, resolved:  ", resolved["preferred"].sum())
print("families, unresolved:", unresolved["preferred"].sum())

print("\nunresolved detail:")
print(unresolved.groupby("LanguageName")["preferred"]
      .sum().sort_values(ascending=False).to_string())

top = (resolved.groupby("canonical")["preferred"]
       .sum().sort_values(ascending=False))

print("\nlanguages after crosswalk:", len(top))
print("\ntop 20:")
print(top.head(20).to_string())

demand = (resolved.groupby(["DistrictName", "canonical"])["preferred"]
          .sum().reset_index()
          .rename(columns={"canonical": "language", "preferred": "families"}))

demand = demand[demand["families"] > 0]
demand.to_csv("data/processed/demand_by_district.csv", index=False)
print("\nwrote", len(demand), "rows to data/processed/demand_by_district.csv")

for dist in DISTRICTS:
    sub = demand[demand["DistrictName"] == dist].nlargest(6, "families")
    print("\n" + dist)
    print(sub[["language", "families"]].to_string(index=False))