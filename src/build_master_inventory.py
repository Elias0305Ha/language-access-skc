"""
Phase 4: unify the seven sector inventories into one table.

Everything downstream (the gap index, the access-desert map, the memo)
reads this file instead of seven files with drifting schemas.

Three things this adds that no sector file has:

  service_scope   A school district is not a city is not a county is not
                  a state. Without this, "12 agencies serve Spanish"
                  silently counts a statewide website and a single food
                  bank as equivalent, which is the error the whole
                  project exists to avoid.

  king_county_authority
                  The memo goes to the King County Language Access
                  Program, which administers KCC 2.15. That ordinance
                  binds King County agencies and county contractors. It
                  does NOT bind school districts, cities, DSHS or
                  WashingtonLawHelp. This column is the line between a
                  compliance finding and regional context, and it has to
                  be explicit or the memo will overclaim.

  tier_verified   Whether a tier 3 has been read by someone who could
                  read it. Two of four checked Amharic offerings were
                  machine output, so an unverified tier 3 is a weaker
                  claim than a verified one and must not look identical.

Schema note. school_inventory.csv predates the multi-sector schema. It is
brought onto it here, additively: no tier is rescored, and the original
file is left untouched.

Output: data/processed/master_inventory.csv
"""

import glob
import os
from pathlib import Path

import pandas as pd

OUT = Path("data/processed/master_inventory.csv")

CORE = ["agency_id", "agency_name", "sector", "service_scope",
        "king_county_authority", "language",
        "written_tier", "oral_tier", "collection_tier",
        "pathway_in_language", "pathway_type",
        "translated_page_count", "quality_verdict", "tier_verified",
        "evidence_url", "capture_date", "notes",
        "assigned_by", "assignment_method"]

# service_scope by agency. Anything not listed defaults by sector.
SCOPE = {
    # county-wide special district
    "kcls": "county",
    # King County departments
    "kcmetro": "county", "health_dph": "county",
    # regional authorities and multi-county providers
    "sound_transit": "regional",
    "health_multicare": "regional", "health_vmfh": "regional",
    "health_seamar": "regional", "health_ichs": "regional",
    "health_neighborcare": "regional", "health_healthpoint": "regional",
    "food_nwharvest": "regional", "food_foodlifeline": "regional",
    "legal_kcba": "county", "legal_solidground": "county",
    "legal_nwirp": "regional", "legal_teamchild": "regional",
    "legal_entrehermanos": "regional", "legal_ccsww": "regional",
    "legal_elap": "county", "legal_colectiva": "regional",
    # single-site or single-city providers
    "health_valleymed": "city", "health_globaltolocal": "city",
    # statewide
    "legal_nwjustice": "state", "legal_walawhelp": "state",
    "food_dshs": "state", "food_waconnection": "state",
    "health_hca": "state", "health_planfinder": "state",
    "health_doh": "state",
}
SCOPE_BY_SECTOR = {"schools": "district", "city": "city", "food": "city"}

# Agencies bound by King County Code Chapter 2.15. County departments and
# the county library system's governing relationship differ, so KCLS is
# deliberately excluded: it is a separate taxing district with its own
# board, not a County agency.
KING_COUNTY_AUTHORITY = {"kcmetro", "health_dph"}

# The school inventory predates agency_id. Built from the district name.
def school_agency_id(name):
    return "school_" + (name.replace(" School District", "")
                        .strip().lower().replace(" ", ""))


def normalise_schools(d):
    d = d.copy()
    d["agency_id"] = d["agency_name"].map(school_agency_id)
    # Every school row was assigned by a person reading a page.
    d["assignment_method"] = "manual"
    # Depth column was named differently before the standard existed.
    d["translated_page_count"] = pd.to_numeric(
        d.get("translated_doc_count"), errors="coerce").fillna(0).astype(int)
    d["collection_tier"] = ""
    d["quality_verdict"] = ""
    # pathway_type did not exist. Derive it from what was recorded, and
    # do not invent precision: a Phase 1 row cannot distinguish an
    # in-language document from a machine widget after the fact, so
    # anything with a pathway is marked unspecified rather than guessed.
    d["pathway_type"] = d.apply(
        lambda r: ("in_language_document" if r["written_tier"] == 3
                   else "pathway_unspecified" if r["pathway_in_language"] is True
                   or str(r["pathway_in_language"]).upper() == "TRUE"
                   else "none"), axis=1)
    return d


def main():
    frames = []
    for f in sorted(glob.glob("data/inventory/*_inventory.csv")):
        name = os.path.basename(f)
        d = pd.read_csv(f)
        if name == "school_inventory.csv":
            d = normalise_schools(d)
        frames.append(d)
        print(f"{name:26} {len(d):>6} rows")

    inv = pd.concat(frames, ignore_index=True)

    # scope
    inv["service_scope"] = inv["agency_id"].map(SCOPE)
    inv["service_scope"] = inv["service_scope"].fillna(
        inv["sector"].map(SCOPE_BY_SECTOR))
    unscoped = inv[inv["service_scope"].isna()]["agency_name"].unique()
    if len(unscoped):
        print(f"\nWARNING unscoped agencies, defaulting to 'regional': {list(unscoped)}")
        inv["service_scope"] = inv["service_scope"].fillna("regional")

    inv["king_county_authority"] = inv["agency_id"].isin(KING_COUNTY_AUTHORITY)

    # tier_verified: only meaningful for a tier 3 claim
    inv["written_tier"] = pd.to_numeric(inv["written_tier"], errors="coerce")
    inv["oral_tier"] = pd.to_numeric(inv["oral_tier"], errors="coerce")
    inv["quality_verdict"] = inv.get("quality_verdict", "").fillna("")
    inv["tier_verified"] = ""
    is3 = inv["written_tier"] == 3
    inv.loc[is3, "tier_verified"] = "unverified"
    inv.loc[is3 & inv["quality_verdict"].isin(["human"]), "tier_verified"] = "verified_human"
    inv.loc[inv["quality_verdict"].eq("machine"), "tier_verified"] = "verified_machine"

    for c in CORE:
        if c not in inv.columns:
            inv[c] = ""
    extras = [c for c in inv.columns if c not in CORE and c != "families"]
    inv = inv[CORE + extras]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    inv.to_csv(OUT, index=False)
    print(f"\nwrote {OUT}  ({len(inv):,} rows, {inv['agency_name'].nunique()} agencies)")

    print("\nrows by sector and scope:")
    print(pd.crosstab(inv["sector"], inv["service_scope"], margins=True).to_string())

    print("\nassessed vs not:")
    print(inv["assignment_method"].value_counts().to_string())

    print("\ntier 3 claims by verification status:")
    print(inv[inv["written_tier"] == 3]["tier_verified"].value_counts().to_string())

    print("\nKing County authority (the memo's compliance scope):")
    kc = inv[inv["king_county_authority"]]
    print(f"  agencies: {sorted(kc['agency_name'].unique())}")
    print(f"  rows: {len(kc):,} of {len(inv):,}")


if __name__ == "__main__":
    main()
