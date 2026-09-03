"""
Pull ACS 5-year table B16001 (Language Spoken at Home by Ability to Speak
English) at PUMA level for Washington State.

B16001 is the detailed table. It names about 40 individual languages
instead of folding them into buckets, which is exactly what the tract-level
table C16001 will not give you. The trade is geography: a PUMA holds
roughly 100,000 people, so a PUMA is several neighbourhoods, not one.

That trade is the whole problem Phase 2 exists to test.

WHY THIS SCRIPT CHUNKS ITS REQUESTS

B16001 has about 128 estimate variables. The Census API caps a request at
50. So a single call cannot fetch the table.

The fix is to split the variable list into batches, request each batch
separately, and join the results back together on the geography columns.
Every batch returns the same PUMAs in the same order, so the join is safe.

This is a normal shape for API work and worth recognising: when a limit
blocks you, the answer is usually to split the request along a dimension
the API does not care about, not to give up on the data.
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
    raise SystemExit("CENSUS_API_KEY not found. Run src/check_key.py first.")

YEAR = 2024
BASE = f"https://api.census.gov/data/{YEAR}/acs/acs5"
STATE_WA = "53"
CHUNK = 45          # under the API's 50-variable cap, with headroom

RAW = Path("data/raw")
REF = Path("data/reference")
RAW.mkdir(parents=True, exist_ok=True)
REF.mkdir(parents=True, exist_ok=True)

OUT_CSV = RAW / f"acs{YEAR}_b16001_wa_pumas.csv"


def get_json(url, params=None, what="request"):
    """GET and decode JSON, with a readable error instead of a stack trace."""
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


if OUT_CSV.exists():
    print(f"already have {OUT_CSV}, delete it to re-download")
    df = pd.read_csv(OUT_CSV, dtype=str)
    print(f"shape: {df.shape}")
    raise SystemExit(0)


# --- part 1: what languages does B16001 actually name? ----------------

print(f"Asking the API what B16001 contains ({YEAR} ACS 5-year)...\n")

meta = get_json(f"{BASE}/groups/B16001.json", what="table metadata")

labels = []
for var, info in meta["variables"].items():
    if var.startswith("B16001_") and var.endswith("E") and not var.endswith("EA"):
        label = info["label"].replace("Estimate!!", "").replace("Total:!!", "")
        labels.append({"variable": var, "label": label})

labels = pd.DataFrame(labels).sort_values("variable").reset_index(drop=True)
labels.to_csv(REF / "b16001_variables.csv", index=False)

# The language headers are the lines without a "speak English" qualifier.
heads = labels[~labels["label"].str.contains("Speak English", na=False)]
print(f"{len(labels)} estimate variables, {len(heads)} language categories.")
print("Saved to data/reference/b16001_variables.csv\n")

print("Languages named by B16001:")
for _, r in heads.iterrows():
    print(f"  {r['variable']}  {r['label']}")


# --- part 2: pull all WA PUMAs, in chunks -----------------------------

est_vars = labels["variable"].tolist()
chunks = [est_vars[i:i + CHUNK] for i in range(0, len(est_vars), CHUNK)]

print(f"\n{len(est_vars)} variables, API cap is 50, so "
      f"{len(chunks)} requests of at most {CHUNK}.")

GEO = ["state", "public use microdata area"]
merged = None

for i, chunk in enumerate(chunks, 1):
    print(f"  request {i} of {len(chunks)} ({len(chunk)} variables)...")
    payload = get_json(
        BASE,
        params={
            "get": ",".join(["NAME"] + chunk),
            "for": "public use microdata area:*",
            "in": f"state:{STATE_WA}",
            "key": KEY,
        },
        what=f"PUMA chunk {i}",
    )
    header, *rows = payload
    part = pd.DataFrame(rows, columns=header)

    if merged is None:
        merged = part
    else:
        # Drop NAME from later chunks so it is not duplicated, then join
        # on the geography columns rather than trusting row order.
        part = part.drop(columns=["NAME"])
        merged = merged.merge(part, on=GEO, how="inner", validate="one_to_one")

print(f"\nshape: {merged.shape}")
print(f"PUMAs returned: {len(merged)}")

with open(RAW / f"acs{YEAR}_b16001_wa_pumas.json", "w") as f:
    json.dump(merged.to_dict(orient="records"), f)
merged.to_csv(OUT_CSV, index=False)
print(f"saved {OUT_CSV}")

# Sanity check: the sum of the language rows should be close to the total.
total = pd.to_numeric(merged["B16001_001E"], errors="coerce").sum()
english = pd.to_numeric(merged["B16001_002E"], errors="coerce").sum()
print(f"\nWashington State, population 5+: {int(total):,}")
print(f"  speak only English:           {int(english):,}")
print(f"  speak another language:       {int(total - english):,}")
