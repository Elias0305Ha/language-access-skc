import pandas as pd
from pathlib import Path

TOP_N = 10

demand = pd.read_csv("data/processed/demand_by_district.csv")

rows = []
for dist, sub in demand.groupby("DistrictName"):
    for _, r in sub.nlargest(TOP_N, "families").iterrows():
        rows.append({
            "agency_name": dist,
            "sector": "schools",
            "language": r["language"],
            "families": r["families"],
            "tier": "",
            "evidence_url": "",
            "capture_date": "",
            "translated_doc_count": "",
            "translated_doc_types": "",
            "pathway_in_language": "",
            "notes": "",
            "assigned_by": "EH",
        })

Path("data/inventory").mkdir(parents=True, exist_ok=True)
pd.DataFrame(rows).to_csv("data/inventory/school_inventory.csv", index=False)
print("wrote", len(rows), "rows to data/inventory/school_inventory.csv")
inv = pd.read_csv("data/inventory/school_inventory.csv")
print(inv[inv["agency_name"].str.startswith("Highline")][["language", "families"]].to_string(index=False))