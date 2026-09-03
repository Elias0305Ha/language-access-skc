"""
Pull ACS 5-year PUMS person records for the five South King County PUMAs.

PUMS is the anonymized person-level microdata behind the ACS. Instead of a
pre-made table, you get one row per surveyed person and count what you want
yourself. Its LANP variable carries 127 specific language codes, including
Amharic, Tigrinya, Oromo, Somali, Dari, Pashto, Marshallese and Chuukese as
separate entries. The published tables (B16001, C16001) collapse all of
those into buckets, which is why this step exists.

Each person carries PWGTP, a sampling weight. One record might represent
20 real people. So you never count rows, you sum the weights.
"""

import os
from pathlib import Path

import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("CENSUS_API_KEY")
if not KEY:
    raise SystemExit("CENSUS_API_KEY not found. Run src/check_key.py first.")

STATE_WA = "53"

PUMAS = {
    "23307": "Auburn",
    "23308": "Federal Way / Des Moines / Vashon",
    "23309": "Kent",
    "23310": "Renton",
    "23311": "Burien / SeaTac / Tukwila / White Center",
}


def get_json(url, params=None, what="request"):
    r = requests.get(url, params=params, timeout=180)
    try:
        return r.json()
    except ValueError:
        raise SystemExit(
            f"\nThe API did not return JSON for the {what}.\n"
            f"HTTP status: {r.status_code}\n"
            f"URL: {r.url.split('&key=')[0]}\n"
            f"Body: {r.text[:600]}\n"
        )


# PUMS lags the summary tables, so find the newest year that answers.
YEAR = None
for year in (2024, 2023, 2022):
    test = requests.get(
        f"https://api.census.gov/data/{year}/acs/acs5/pums",
        params={"get": "PWGTP", "for": f"state:{STATE_WA}",
                "PUMA": "23309", "key": KEY},
        timeout=120,
    )
    if test.status_code == 200 and test.text.strip().startswith("["):
        YEAR = year
        break

if YEAR is None:
    raise SystemExit("No PUMS year responded. Check src/check_key.py.")

print(f"using {YEAR} ACS 5-year PUMS\n")
BASE = f"https://api.census.gov/data/{YEAR}/acs/acs5/pums"

# LANP is stored as a numeric code. Fetch the code-to-name lookup.
meta = get_json(f"{BASE}/variables/LANP.json", what="LANP labels")
CODE2LANG = meta.get("values", {}).get("item", {})
if not CODE2LANG:
    raise SystemExit("Could not read LANP labels. The metadata shape changed.")
print(f"{len(CODE2LANG)} language codes available\n")

frames = []
for code, nickname in PUMAS.items():
    print(f"  pulling PUMA {code}  {nickname} ...")
    payload = get_json(
        BASE,
        params={"get": "LANP,PWGTP", "for": f"state:{STATE_WA}",
                "PUMA": code, "key": KEY},
        what=f"PUMA {code}",
    )
    header, *rows = payload
    d = pd.DataFrame(rows, columns=header)
    d["puma"] = code
    frames.append(d)

pums = pd.concat(frames, ignore_index=True)
print(f"\n{len(pums):,} person records pulled")

pums["PWGTP"] = pd.to_numeric(pums["PWGTP"], errors="coerce")

# LANP's not-applicable code covers people who speak only English, plus
# children under 5 and group-quarters/vacant records. Its label is
# "N/A (GQ/vacant)". It is not a language, and an empty-string check does
# not catch it because the API returns a real code.
pums["language"] = pums["LANP"].astype(str).map(CODE2LANG)

before = len(pums)
pums = pums[~pums["language"].fillna("").str.startswith("N/A")]
print(f"{before - len(pums):,} records dropped as not-applicable")
print(f"{len(pums):,} records speak a language other than English at home")

# Sum weights, never count rows.
out = (pums.groupby(["puma", "language"])["PWGTP"].sum()
       .reset_index().rename(columns={"PWGTP": "people"}))
out["puma_name"] = out["puma"].map(PUMAS)
out = out.sort_values(["puma", "people"], ascending=[True, False])

Path("data/processed").mkdir(parents=True, exist_ok=True)
out.to_csv("data/processed/pums_language_by_puma.csv", index=False)
print("\nwrote data/processed/pums_language_by_puma.csv")

for code, nickname in PUMAS.items():
    sub = out[out["puma"] == code]
    total = sub["people"].sum()
    print(f"\n=== {code}  {nickname} ===")
    print(f"    {int(total):,} people speak a language other than English")
    print(sub.head(12)[["language", "people"]].to_string(index=False))

# The languages this project cares about, wherever they appear.
WATCH = ["Amharic", "Tigrinya", "Oromo", "Somali", "Dari", "Pashto",
         "Punjabi", "Ukrainian", "Marshallese", "Chuukese", "Vietnamese",
         "Portuguese", "Burmese", "Arabic", "Swahili"]

print("\n\n=== PRIORITY LANGUAGES ACROSS ALL FIVE PUMAS ===")
watch = (out[out["language"].isin(WATCH)]
         .pivot_table(index="language", columns="puma",
                      values="people", aggfunc="sum", fill_value=0))
watch["TOTAL"] = watch.sum(axis=1)
print(watch.sort_values("TOTAL", ascending=False).astype(int).to_string())
