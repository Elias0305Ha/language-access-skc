"""
Pull ACS 5-year table C16001 (Language Spoken at Home for the Population
5 Years and Over) at census tract level for King County, WA.

Runs in two parts on purpose:

  1. Ask the API what is actually in C16001 and print it. Never build a
     query around variable numbers you remembered. The API is the
     authority on its own schema and it costs one request to ask.

  2. Use that list to pull every tract in King County, and save it.

Why part 2 names its variables instead of asking for group(C16001):
the API caps a request at 50 variables. A group request expands to the
estimate, the margin of error, and two annotation columns for each of the
38 variables, about 152 columns, which is over the cap. The API rejects it
with a plain-text sentence while still returning HTTP 200, so resp.json()
fails on a message rather than on data. Naming the 38 estimates keeps the
request at 39 columns and under the limit.

C16001 gives 12 language groups at tract level, which is finer than the
four-bucket table (C16002) and means Vietnamese, Chinese, Korean, Tagalog
and Arabic need no apportionment at all. The languages that DO need it are
folded into the residual groups: Dari, Pashto and Punjabi inside Other
Indo-European; Amharic, Tigrinya and Somali inside Other and unspecified;
Marshallese and Chuukese inside Other Asian and Pacific Island.
"""

import os
import json
from pathlib import Path

import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("CENSUS_API_KEY")
if not KEY:
    raise SystemExit(
        "CENSUS_API_KEY not found.\n"
        "Check that .env exists in the project root and contains one line:\n"
        "  CENSUS_API_KEY=yourkeyhere"
    )

YEAR = 2024
BASE = f"https://api.census.gov/data/{YEAR}/acs/acs5"
STATE_WA = "53"
COUNTY_KING = "033"

RAW = Path("data/raw")
REF = Path("data/reference")
RAW.mkdir(parents=True, exist_ok=True)
REF.mkdir(parents=True, exist_ok=True)


def get_json(url, params=None, what="request"):
    """
    GET and decode JSON, with a readable error instead of a stack trace.

    The Census API answers some bad requests with a plain-text sentence and
    an HTTP 200. Calling .json() on that raises a decode error that says
    nothing useful about the real problem, so this prints the body.
    """
    resp = requests.get(url, params=params, timeout=120)
    try:
        return resp.json()
    except ValueError:
        raise SystemExit(
            f"\nThe API did not return JSON for the {what}.\n"
            f"HTTP status: {resp.status_code}\n"
            f"URL: {resp.url.split('&key=')[0]}\n"
            f"Body: {resp.text[:600]}\n"
        )


# --- part 1: what is in this table? -----------------------------------

print(f"Asking the API what C16001 contains ({YEAR} ACS 5-year)...\n")

meta = get_json(f"{BASE}/groups/C16001.json", what="table metadata")

labels = []
for var, info in meta["variables"].items():
    # Estimates end in E. Margins end in M. Annotations end in EA or MA.
    if var.startswith("C16001_") and var.endswith("E") and not var.endswith("EA"):
        labels.append({
            "variable": var,
            "label": info["label"].replace("Estimate!!", "").replace("Total:!!", ""),
        })

labels = pd.DataFrame(labels).sort_values("variable").reset_index(drop=True)
labels.to_csv(REF / "c16001_variables.csv", index=False)

print(f"{len(labels)} estimate variables. Saved to "
      f"data/reference/c16001_variables.csv")


# --- part 2: pull every King County tract -----------------------------

est_vars = labels["variable"].tolist()
get_list = ["NAME"] + est_vars

print(f"\nRequesting {len(get_list)} columns (API cap is 50).")
print("Pulling C16001 for all tracts in King County, WA...")

payload = get_json(
    BASE,
    params={
        "get": ",".join(get_list),
        "for": "tract:*",
        "in": f"state:{STATE_WA} county:{COUNTY_KING}",
        "key": KEY,
    },
    what="tract data pull",
)

# Freeze the exact API response, same discipline as the OSPI file.
with open(RAW / f"acs{YEAR}_c16001_king_tracts.json", "w") as f:
    json.dump(payload, f)

header, *rows = payload
df = pd.DataFrame(rows, columns=header)

df.to_csv(RAW / f"acs{YEAR}_c16001_king_tracts.csv", index=False)

print(f"\nshape: {df.shape}")
print(f"tracts returned: {df['tract'].nunique()}")
print(f"saved data/raw/acs{YEAR}_c16001_king_tracts.csv")

# Quick sanity check: county totals for the groups that matter to you.
check = {
    "C16001_001E": "total population 5+",
    "C16001_003E": "Spanish",
    "C16001_012E": "Russian, Polish, Slavic",
    "C16001_015E": "Other Indo-European",
    "C16001_024E": "Vietnamese",
    "C16001_030E": "Other Asian and Pacific Island",
    "C16001_036E": "Other and unspecified",
}
print("\nKing County totals, sanity check:")
for var, name in check.items():
    total = pd.to_numeric(df[var], errors="coerce").sum()
    print(f"  {name:<32} {int(total):>10,}")
