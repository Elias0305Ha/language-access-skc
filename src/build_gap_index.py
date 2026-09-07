"""
Phase 4: the gap index. Demand joined to supply across all seven sectors,
at district x language.

The question this answers, precisely:

    For a family in district D speaking language L, what public services
    can actually reach them in L, how close are those services, and how
    much of that provision is a machine guess rather than a human
    translation?

Three design decisions, all constants at the top so the Phase 4
sensitivity sweep can move them without touching logic.

1. PROVISION IS WEIGHTED BY DISTANCE OF AUTHORITY.
   A statewide website and the school district that sends your child's
   placement letter both "serve" you, and they are not equivalent. The
   district is the one with your address. Weighting by service_scope
   keeps the index from being flattered by statewide resources that no
   local agency points anyone toward.

2. CITY PROVISION IS WEIGHTED BY SPATIAL OVERLAP.
   Seven of the eight study cities span more than one school district.
   Des Moines is 69.8% Highline and 30.2% Federal Way. So a Des Moines
   city page counts fully toward Highline and partially toward Federal
   Way, from the measured overlap, not from a guess.

3. THE INDEX IS REPORTED TWICE.
   155 tier-3 claims exist in this dataset and 2 have been read by
   someone who could read the language. Two of the four Amharic
   offerings that WERE checked turned out to be machine output. So the
   optimistic reading takes every tier 3 at face value, and the
   conservative reading discounts unverified ones. The truth is a range,
   and publishing a single number would be false precision.

Output: outputs/gap_index_phase4.csv
        outputs/gap_index_phase4_by_language.csv
"""

from pathlib import Path

import pandas as pd

# ---- tuning constants -------------------------------------------------

# Fraction of need still unmet at each tier. Carried forward unchanged
# from build_gap_table.py so Phase 1 and Phase 4 remain comparable.
SHORTFALL_WRITTEN = {3: 0.0, 2: 0.60, 1: 0.85, 0: 1.0}
SHORTFALL_ORAL = {3: 0.0, 2: 0.20, 1: 0.70, 0: 1.0}
W_WRITTEN, W_ORAL = 0.7, 0.3

# How much a provision counts, by how close the authority is to the
# family. A district or city agency is the one that sends you letters and
# that you walk into. A statewide website is real but nobody hands it to
# you. These are judgments; sweep them.
SCOPE_WEIGHT = {
    "district": 1.00,
    "city":     0.90,
    "county":   0.70,
    "regional": 0.50,
    "state":    0.35,
}

# A city barely clipping a district should not count as serving it.
MIN_CITY_OVERLAP_PCT = 5.0

# Conservative reading: an unverified tier 3 is treated as this tier
# instead. 2 of 4 checked Amharic offerings were machine output, so 2 is
# a defensible midpoint between trusting it (3) and assuming machine (1).
UNVERIFIED_TIER3_AS = 2

MASTER = Path("data/processed/master_inventory.csv")
OVERLAP = Path("data/processed/city_district_overlap.csv")
DEMAND = Path("data/processed/demand_by_district.csv")
OUT = Path("outputs/gap_index_phase4.csv")
OUT_LANG = Path("outputs/gap_index_phase4_by_language.csv")

DISTRICTS = ["Auburn School District", "Federal Way School District",
             "Highline School District", "Kent School District",
             "Renton School District", "Tukwila School District"]


def agency_reach(inv, overlap):
    """One row per (district, agency, language) with a reach weight.

    Reach is how much this agency's provision counts for this district:
      district-scope  the district itself only
      city-scope      the districts its city overlaps, scaled by overlap
      wider scopes    every district, scaled by SCOPE_WEIGHT
    """
    rows = []

    # School districts serve themselves.
    d = inv[inv["service_scope"] == "district"]
    for r in d.itertuples():
        rows.append((r.agency_name, r.language, r.agency_name, 1.0, r))

    # Cities serve the districts they overlap.
    city_map = {}
    for r in overlap.itertuples():
        if r.pct_of_city_in_district >= MIN_CITY_OVERLAP_PCT:
            city_map.setdefault(f"City of {r.city}", []).append(
                (r.district_name, r.pct_of_city_in_district / 100.0))
    c = inv[inv["service_scope"] == "city"]
    for r in c.itertuples():
        for dist, frac in city_map.get(r.agency_name, []):
            rows.append((r.agency_name, r.language, dist,
                         SCOPE_WEIGHT["city"] * frac, r))

    # County, regional and state agencies serve every district.
    w = inv[inv["service_scope"].isin(["county", "regional", "state"])]
    for r in w.itertuples():
        for dist in DISTRICTS:
            rows.append((r.agency_name, r.language, dist,
                         SCOPE_WEIGHT[r.service_scope], r))
    return rows


def main():
    inv = pd.read_csv(MASTER)
    overlap = pd.read_csv(OVERLAP)
    demand = pd.read_csv(DEMAND)

    # Unassessed agencies must not read as zero provision.
    assessed = inv[inv["assignment_method"] != "unreachable"].copy()
    print(f"inventory rows: {len(inv):,}  assessed: {len(assessed):,}  "
          f"excluded as unreachable: {len(inv) - len(assessed):,}")

    assessed["written_tier"] = pd.to_numeric(assessed["written_tier"], errors="coerce")
    assessed["oral_tier"] = pd.to_numeric(assessed["oral_tier"], errors="coerce")
    assessed = assessed.dropna(subset=["written_tier", "oral_tier"])

    # Conservative variant of the written tier.
    assessed["written_tier_cons"] = assessed["written_tier"]
    unver = (assessed["written_tier"] == 3) & (assessed["tier_verified"] != "verified_human")
    assessed.loc[unver, "written_tier_cons"] = UNVERIFIED_TIER3_AS
    print(f"tier-3 rows discounted in the conservative reading: {int(unver.sum())}")

    reach = agency_reach(assessed, overlap)
    print(f"district-agency-language reach rows: {len(reach):,}")

    rec = {}
    for agency, lang, dist, weight, r in reach:
        key = (dist, lang)
        e = rec.setdefault(key, {
            "best_written": 0, "best_oral": 0, "best_written_cons": 0,
            "best_written_local": 0, "best_written_local_cons": 0,
            "n_agencies_tier3": 0,
            "n_verified_tier3": 0, "providers": [], "best_agency": None,
            "best_weighted": -1.0,
        })
        # Weighted provision: a tier 3 from a distant agency is worth less
        # than a tier 3 from the district itself.
        wv = r.written_tier * weight
        if wv > e["best_weighted"]:
            e["best_weighted"] = wv
            e["best_agency"] = agency
        e["best_written"] = max(e["best_written"], r.written_tier)
        e["best_written_cons"] = max(e["best_written_cons"], r.written_tier_cons)
        e["best_oral"] = max(e["best_oral"], r.oral_tier)
        # "Local" means the district itself or a city substantially inside
        # it: the agencies that send you letters and that you walk into.
        if weight >= SCOPE_WEIGHT["city"] * 0.5:
            e["best_written_local"] = max(e["best_written_local"], r.written_tier)
            e["best_written_local_cons"] = max(
                e.get("best_written_local_cons", 0), r.written_tier_cons)
        if r.written_tier == 3:
            e["n_agencies_tier3"] += 1
            e["providers"].append(agency)
            if r.tier_verified == "verified_human":
                e["n_verified_tier3"] += 1

    fam = {(r.DistrictName, r.language): r.families for r in demand.itertuples()}

    rows = []
    for (dist, lang), e in rec.items():
        families = fam.get((dist, lang), 0)
        if not families:
            continue                      # no measured demand in this district
        for label, wt, lt in (("optimistic", e["best_written"],
                               e["best_written_local"]),
                              ("conservative", e["best_written_cons"],
                               e["best_written_local_cons"])):
            wg = families * SHORTFALL_WRITTEN[int(wt)]
            og = families * SHORTFALL_ORAL[int(e["best_oral"])]
            score = round(W_WRITTEN * wg + W_ORAL * og, 1)
            rows.append({
                "district": dist, "language": lang, "families": families,
                "reading": label,
                "best_written_tier": int(wt),
                "best_written_tier_local_only": int(lt),
                "best_oral_tier": int(e["best_oral"]),
                "agencies_at_tier3": e["n_agencies_tier3"],
                "verified_tier3": e["n_verified_tier3"],
                "best_provider": e["best_agency"],
                "providers_at_tier3": "; ".join(sorted(set(e["providers"]))[:6]),
                "written_gap": round(wg, 1), "oral_gap": round(og, 1),
                "gap_score": score,
                "severity": round(score / families, 3),
                "families_no_written_anywhere": families if wt == 0 else 0,
                "families_no_local_written": families if lt == 0 else 0,
                # The measure that matters. A city running a Google
                # Translate widget scores tier 1, which is not zero and
                # is not a document. "No local DOCUMENT" is the honest
                # analogue of the Phase 1 headline.
                "families_no_local_document": families if lt < 3 else 0,
            })

    gap = pd.DataFrame(rows).sort_values(
        ["reading", "gap_score"], ascending=[True, False])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    gap.to_csv(OUT, index=False)
    print(f"\nwrote {OUT}  ({len(gap):,} rows)")

    opt = gap[gap["reading"] == "optimistic"]
    con = gap[gap["reading"] == "conservative"]

    print("\n=== HEADLINE, both readings ===")
    print(f"district-language pairs with measured demand: {len(opt):,}")
    print(f"families covered: {opt['families'].sum():,}")
    print(f"\nfamilies with NO written provision from ANY agency, any sector:")
    print(f"   optimistic   {opt['families_no_written_anywhere'].sum():>7,}")
    print(f"   conservative {con['families_no_written_anywhere'].sum():>7,}")
    print(f"\nfamilies with NO local written provision at all, any tier "
          f"(own district or a city substantially inside it):")
    print(f"   optimistic   {opt['families_no_local_written'].sum():>7,}")
    print(f"   conservative {con['families_no_local_written'].sum():>7,}")
    # The measure that matters. A city running a Google Translate widget
    # scores tier 1, which is not zero and is also not a document.
    # "No local human-translated document" is the honest analogue of the
    # Phase 1 headline of 1,428 families.
    print(f"\nfamilies with no local human-translated DOCUMENT "
          f"(local best below tier 3):")
    print(f"   optimistic   {opt['families_no_local_document'].sum():>7,}")
    print(f"   conservative {con['families_no_local_document'].sum():>7,}")

    print("\n=== WORST 15, conservative reading ===")
    top = con.head(15)
    print(top[["district", "language", "families", "best_written_tier",
               "best_oral_tier", "best_written_tier_local_only",
               "gap_score", "severity"]].to_string(index=False))

    bylang = (opt.groupby("language")
              .agg(families=("families", "sum"),
                   districts=("district", "nunique"),
                   gap_score=("gap_score", "sum"),
                   no_local_any=("families_no_local_written", "sum"),
                   no_local_document=("families_no_local_document", "sum"))
              .sort_values("gap_score", ascending=False))
    bylang.to_csv(OUT_LANG)
    print(f"\nwrote {OUT_LANG}")
    print("\n=== WORST 15 LANGUAGES, region-wide, optimistic ===")
    print(bylang.head(15).to_string())


if __name__ == "__main__":
    main()
