"""
Phase 4: the gap index. Demand joined to supply across all seven sectors,
at district x language.

The question this answers, precisely:

    For a family in district D speaking language L, what public services
    can actually reach them in L, how close are those services, and how
    much of that provision is a machine guess rather than a human
    translation?

Three design decisions, all in DEFAULT_PARAMS so sensitivity_analysis.py
can sweep them without touching logic.

1. PROVISION IS WEIGHTED BY DISTANCE OF AUTHORITY.
   A statewide website and the school district that sends your child's
   placement letter both "serve" you, and they are not equivalent.
   Weighting by service_scope keeps the index from being flattered by
   statewide resources no local agency points anyone toward.

2. CITY PROVISION IS WEIGHTED BY SPATIAL OVERLAP.
   Seven of the eight study cities span more than one school district.
   Des Moines is 69.8% Highline and 30.2% Federal Way, measured, not
   guessed.

3. THE INDEX IS REPORTED TWICE.
   155 tier-3 claims exist and 2 have been read by someone who could read
   the language. Two of the four Amharic offerings that were checked
   turned out to be machine output. The optimistic reading takes every
   tier 3 at face value; the conservative reading discounts unverified
   ones. The truth is a range, and one number would be false precision.

Output: outputs/gap_index_phase4.csv
        outputs/gap_index_phase4_by_language.csv
"""

from pathlib import Path

import pandas as pd

MASTER = Path("data/processed/master_inventory.csv")
OVERLAP = Path("data/processed/city_district_overlap.csv")
DEMAND = Path("data/processed/demand_by_district.csv")
OUT = Path("outputs/gap_index_phase4.csv")
OUT_LANG = Path("outputs/gap_index_phase4_by_language.csv")

DISTRICTS = ["Auburn School District", "Federal Way School District",
             "Highline School District", "Kent School District",
             "Renton School District", "Tukwila School District"]

DEFAULT_PARAMS = {
    # Fraction of need still unmet at each tier. Carried forward unchanged
    # from Phase 1 so the two phases stay comparable.
    "shortfall_written": {3: 0.0, 2: 0.60, 1: 0.85, 0: 1.0},
    "shortfall_oral": {3: 0.0, 2: 0.20, 1: 0.70, 0: 1.0},
    "w_written": 0.7,
    "w_oral": 0.3,
    # How much a provision counts, by how close the authority sits to the
    # family. Judgments, and swept in the sensitivity analysis.
    "scope_weight": {"district": 1.00, "city": 0.90, "county": 0.70,
                     "regional": 0.50, "state": 0.35},
    # A city barely clipping a district does not count as serving it.
    "min_city_overlap_pct": 5.0,
    # Conservative reading: an unverified tier 3 is treated as this tier.
    # 2 of 4 checked offerings were machine output, so 2 sits between
    # trusting it (3) and assuming the worst (1).
    "unverified_tier3_as": 2,
}


def load_inputs():
    """Frozen inputs, shared by the index and the sensitivity sweep."""
    inv = pd.read_csv(MASTER)
    overlap = pd.read_csv(OVERLAP)
    demand = pd.read_csv(DEMAND)
    # Unassessed agencies must never read as zero provision.
    assessed = inv[inv["assignment_method"] != "unreachable"].copy()
    assessed["written_tier"] = pd.to_numeric(assessed["written_tier"], errors="coerce")
    assessed["oral_tier"] = pd.to_numeric(assessed["oral_tier"], errors="coerce")
    assessed = assessed.dropna(subset=["written_tier", "oral_tier"])
    return inv, assessed, overlap, demand


def agency_reach(inv, overlap, params):
    """(agency, language, district, weight, row) for every reachable pair."""
    sw = params["scope_weight"]
    rows = []

    for r in inv[inv["service_scope"] == "district"].itertuples():
        rows.append((r.agency_name, r.language, r.agency_name, 1.0, r))

    city_map = {}
    for r in overlap.itertuples():
        if r.pct_of_city_in_district >= params["min_city_overlap_pct"]:
            city_map.setdefault(f"City of {r.city}", []).append(
                (r.district_name, r.pct_of_city_in_district / 100.0))
    for r in inv[inv["service_scope"] == "city"].itertuples():
        for dist, frac in city_map.get(r.agency_name, []):
            rows.append((r.agency_name, r.language, dist, sw["city"] * frac, r))

    wide = inv[inv["service_scope"].isin(["county", "regional", "state"])]
    for r in wide.itertuples():
        for dist in DISTRICTS:
            rows.append((r.agency_name, r.language, dist, sw[r.service_scope], r))
    return rows


def compute_index(assessed, overlap, demand, params):
    """Return the gap index for one parameter set, both readings."""
    a = assessed.copy()
    a["written_tier_cons"] = a["written_tier"]
    unver = (a["written_tier"] == 3) & (a["tier_verified"] != "verified_human")
    a.loc[unver, "written_tier_cons"] = params["unverified_tier3_as"]

    # "Local" means the district itself or a city substantially inside it:
    # the agencies that send you letters and that you walk into.
    local_cut = params["scope_weight"]["city"] * 0.5

    rec = {}
    for agency, lang, dist, weight, r in agency_reach(a, overlap, params):
        e = rec.setdefault((dist, lang), {
            "best_written": 0, "best_oral": 0, "best_written_cons": 0,
            "best_local": 0, "best_local_cons": 0,
            "n_tier3": 0, "n_verified": 0, "providers": [],
            "best_agency": None, "best_weighted": -1.0})
        wv = r.written_tier * weight
        if wv > e["best_weighted"]:
            e["best_weighted"], e["best_agency"] = wv, agency
        e["best_written"] = max(e["best_written"], r.written_tier)
        e["best_written_cons"] = max(e["best_written_cons"], r.written_tier_cons)
        e["best_oral"] = max(e["best_oral"], r.oral_tier)
        if weight >= local_cut:
            e["best_local"] = max(e["best_local"], r.written_tier)
            e["best_local_cons"] = max(e["best_local_cons"], r.written_tier_cons)
        if r.written_tier == 3:
            e["n_tier3"] += 1
            e["providers"].append(agency)
            if r.tier_verified == "verified_human":
                e["n_verified"] += 1

    fam = {(r.DistrictName, r.language): r.families for r in demand.itertuples()}
    sw, so = params["shortfall_written"], params["shortfall_oral"]
    ww, wo = params["w_written"], params["w_oral"]

    rows = []
    for (dist, lang), e in rec.items():
        families = fam.get((dist, lang), 0)
        if not families:
            continue                       # no measured demand here
        for label, wt, lt in (("optimistic", e["best_written"], e["best_local"]),
                              ("conservative", e["best_written_cons"], e["best_local_cons"])):
            wg = families * sw[int(wt)]
            og = families * so[int(e["best_oral"])]
            score = round(ww * wg + wo * og, 1)
            rows.append({
                "district": dist, "language": lang, "families": families,
                "reading": label,
                "best_written_tier": int(wt),
                "best_written_tier_local_only": int(lt),
                "best_oral_tier": int(e["best_oral"]),
                "agencies_at_tier3": e["n_tier3"],
                "verified_tier3": e["n_verified"],
                "best_provider": e["best_agency"],
                "providers_at_tier3": "; ".join(sorted(set(e["providers"]))[:6]),
                "written_gap": round(wg, 1), "oral_gap": round(og, 1),
                "gap_score": score,
                "severity": round(score / families, 3),
                "families_no_written_anywhere": families if wt == 0 else 0,
                "families_no_local_written": families if lt == 0 else 0,
                # The measure that matters. A city running a Google
                # Translate widget scores tier 1, which is not zero and is
                # also not a document. This is the honest analogue of the
                # Phase 1 headline of 1,428 families.
                "families_no_local_document": families if lt < 3 else 0,
            })
    return pd.DataFrame(rows)


def main():
    inv, assessed, overlap, demand = load_inputs()
    print(f"inventory rows: {len(inv):,}  assessed: {len(assessed):,}  "
          f"excluded as unreachable: {len(inv) - len(assessed):,}")

    gap = compute_index(assessed, overlap, demand, DEFAULT_PARAMS)
    gap = gap.sort_values(["reading", "gap_score"], ascending=[True, False])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    gap.to_csv(OUT, index=False)
    print(f"wrote {OUT}  ({len(gap):,} rows)")

    opt = gap[gap["reading"] == "optimistic"]
    con = gap[gap["reading"] == "conservative"]

    print("\n=== HEADLINE ===")
    print(f"district-language pairs with measured demand: {len(opt):,}")
    print(f"families covered: {opt['families'].sum():,}")
    print(f"\nno written provision from ANY agency, any sector, any tier:")
    print(f"   {opt['families_no_written_anywhere'].sum():>7,} families")
    print(f"\nno local human-translated DOCUMENT:")
    print(f"   optimistic   {opt['families_no_local_document'].sum():>7,}")
    print(f"   conservative {con['families_no_local_document'].sum():>7,}")

    print("\n=== WORST 12, conservative ===")
    print(con.head(12)[["district", "language", "families",
                        "best_written_tier", "best_oral_tier",
                        "gap_score", "severity"]].to_string(index=False))

    bylang = (opt.groupby("language")
              .agg(families=("families", "sum"),
                   districts=("district", "nunique"),
                   gap_score=("gap_score", "sum"),
                   no_local_document=("families_no_local_document", "sum"))
              .sort_values("gap_score", ascending=False))
    bylang.to_csv(OUT_LANG)
    print(f"\nwrote {OUT_LANG}")
    print("\n=== WORST 12 LANGUAGES, region-wide ===")
    print(bylang.head(12).to_string())


if __name__ == "__main__":
    main()
