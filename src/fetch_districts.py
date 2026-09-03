"""
Pull ACS 5-year C16001 at SCHOOL DISTRICT level for the six study districts.

The ACS publishes "school district (unified)" as a geography, so the
language buckets can be fetched for exactly the areas where OSPI gives
ground truth. No spatial join, no shapefiles, no overlap assumptions.

This is the denominator for the apportionment test. The bucket totals come
from here, the within-bucket language shares come from PUMS, and OSPI says
what the real answer is.
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

YEAR = 2024
BASE = f"https://api.census.gov/data/{YEAR}/acs/acs5"
STATE_WA = "53"

STUDY = ["Highline", "Tukwila", "Kent", "Federal Way", "Renton", "Auburn"]

BUCKETS = {
    "C16001_001E": "total 5+",
    "C16001_002E": "English only",
    "C16001_003E": "Spanish",
    "C16001_012E": "Russian/Polish/Slavic",
    "C16001_015E": "Other Indo-European",
    "C16001_021E": "Chinese",
    "C16001_024E": "Vietnamese",
    "C16001_027E": "Tagalog",
    "C16001_030E": "Other Asian & Pacific Island",
    "C16001_033E": "Arabic",
    "C16001_036E": "Other and unspecified",
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


# Reuse the variable list the tract pull already saved.
labels = pd.read_csv("data/reference/c16001_variables.csv")
est_vars = labels["variable"].tolist()

print(f"Pulling C16001 for all WA unified school districts "
      f"({len(est_vars) + 1} columns)...")

payload = get_json(
    BASE,
    params={
        "get": ",".join(["NAME"] + est_vars),
        "for": "school district (unified):*",
        "in": f"state:{STATE_WA}",
        "key": KEY,
    },
    what="school district pull",
)

header, *rows = payload
df = pd.DataFrame(rows, columns=header)
print(f"{len(df)} unified school districts in Washington\n")

Path("data/raw").mkdir(parents=True, exist_ok=True)
df.to_csv(f"data/raw/acs{YEAR}_c16001_wa_school_districts.csv", index=False)

# Match our six by name, and show every match so nothing is picked up
# silently. A substring match can grab a district you did not mean.
pattern = "|".join(STUDY)
ours = df[df["NAME"].str.contains(pattern, case=False, na=False)].copy()

print(f"{len(ours)} districts matched the study names:")
for _, r in ours.iterrows():
    print(f"  {r['NAME']}")

for col in est_vars:
    ours[col] = pd.to_numeric(ours[col], errors="coerce")

print("\n=== LANGUAGE BUCKETS, whole population 5 and over ===")
show = ours[["NAME"] + list(BUCKETS)].copy()
show.columns = ["district"] + list(BUCKETS.values())
show["district"] = show["district"].str.replace(
    " School District, Washington", "", regex=False)
print(show.set_index("district").astype(int).to_string())
