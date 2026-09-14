"""
Phase 5: export a star-schema model for Power BI.

Why a star schema rather than handing Power BI the wide tables. The
analysis tables are denormalised on purpose: master_inventory repeats an
agency's name and sector on every one of its ~130 language rows. Loading
that directly gives a model where filtering by sector, language and
district all fight each other through one flat table, measures get slow,
and the relationship diagram tells a reviewer nothing about whether the
author understands modelling.

The shape exported here:

    dim_language ----+
    dim_agency ------+--> fact_provision      (agency x language)
    dim_district ----+--> fact_gap            (district x language x reading)
                     +--> fact_service_point  (physical locations)
                          bridge_point_language (a point serves N languages)

One row per grain, dimensions joined by key, one bridge for the
many-to-many between a physical location and the languages it serves.
That last one is the piece worth being able to explain in an interview:
a library branch holds several language collections, and a language is
held at several branches, so it cannot be a direct relationship.

Output: powerbi/*.csv  plus powerbi/measures.dax
"""

from pathlib import Path

import pandas as pd

OUT = Path("powerbi")


def main():
    OUT.mkdir(exist_ok=True)

    inv = pd.read_csv("data/processed/master_inventory.csv")
    gap = pd.read_csv("outputs/gap_index_phase4.csv")
    demand = pd.read_csv("data/processed/demand_by_district.csv")
    tiers = pd.read_csv("outputs/kc_tier_map_vs_demand.csv")
    points = pd.read_csv("data/processed/service_points.csv")
    overlap = pd.read_csv("data/processed/city_district_overlap.csv")
    deserts = pd.read_csv("outputs/access_deserts.csv")

    # ---- dim_language ------------------------------------------------
    fam = demand.groupby("language")["families"].sum()
    lang = tiers.rename(columns={"families_south_king_county": "families_total"})
    lang = lang[["language", "families_total", "kc_tier", "kc_status",
                 "on_tier_map"]].copy()
    # Languages present in supply but with no measured demand still need a
    # key, or provision rows for them would orphan.
    extra = sorted(set(inv["language"]) - set(lang["language"]))
    if extra:
        lang = pd.concat([lang, pd.DataFrame({
            "language": extra, "families_total": 0, "kc_tier": "",
            "kc_status": "NOT ON THE TIER MAP", "on_tier_map": False})],
            ignore_index=True)
    lang["families_total"] = lang["families_total"].fillna(0).astype(int)
    lang["demand_rank"] = lang["families_total"].rank(
        ascending=False, method="min").astype(int)
    lang.to_csv(OUT / "dim_language.csv", index=False)

    # ---- dim_agency --------------------------------------------------
    ag = (inv.groupby(["agency_id", "agency_name", "sector", "service_scope",
                       "king_county_authority"], dropna=False)
          .agg(languages_scored=("language", "nunique"),
               languages_at_tier3=("written_tier",
                                   lambda s: int((pd.to_numeric(s, errors="coerce") == 3).sum())),
               assessment=("assignment_method", "first"))
          .reset_index())
    ag["assessed"] = ag["assessment"] != "unreachable"
    ag.to_csv(OUT / "dim_agency.csv", index=False)

    # ---- dim_district ------------------------------------------------
    dist = (demand.groupby("DistrictName")
            .agg(families_total=("families", "sum"),
                 languages_reported=("language", "nunique"))
            .reset_index().rename(columns={"DistrictName": "district"}))
    cities = (overlap[overlap["pct_of_city_in_district"] >= 5]
              .groupby("district_name")["city"]
              .apply(lambda s: ", ".join(sorted(s))).rename("cities_overlapping"))
    dist = dist.merge(cities, left_on="district", right_index=True, how="left")
    dist.to_csv(OUT / "dim_district.csv", index=False)

    # ---- fact_provision ----------------------------------------------
    prov = inv[["agency_id", "language", "sector", "written_tier", "oral_tier",
                "collection_tier", "pathway_type", "translated_page_count",
                "quality_verdict", "tier_verified", "assignment_method",
                "evidence_url", "capture_date"]].copy()
    for c in ("written_tier", "oral_tier"):
        prov[c] = pd.to_numeric(prov[c], errors="coerce")
    prov.to_csv(OUT / "fact_provision.csv", index=False)

    # ---- fact_gap ----------------------------------------------------
    gap.to_csv(OUT / "fact_gap.csv", index=False)

    # ---- fact_service_point + bridge ---------------------------------
    pts = points.copy()
    pts["languages_served"] = pts["languages_served"].fillna("")
    bridge = []
    for r in pts.itertuples():
        for lg in [x.strip() for x in str(r.languages_served).split(";") if x.strip()]:
            bridge.append({"location_id": r.location_id, "language": lg})
    pd.DataFrame(bridge).drop_duplicates().to_csv(
        OUT / "bridge_point_language.csv", index=False)
    pts.drop(columns=["languages_served"]).to_csv(
        OUT / "fact_service_point.csv", index=False)

    # ---- fact_access_desert ------------------------------------------
    deserts.to_csv(OUT / "fact_access_desert.csv", index=False)

    # ---- measures ----------------------------------------------------
    (OUT / "measures.dax").write_text(MEASURES, encoding="utf-8")

    print(f"wrote {OUT}/ :")
    for f in sorted(OUT.glob("*")):
        n = sum(1 for _ in open(f, encoding="utf-8")) - 1 if f.suffix == ".csv" else ""
        print(f"   {f.name:30} {n if n != '' else ''}")
    print("\nrelationships to create in Power BI:")
    print("   dim_language[language]  1 -> *  fact_provision[language]")
    print("   dim_language[language]  1 -> *  fact_gap[language]")
    print("   dim_language[language]  1 -> *  fact_access_desert[language]")
    print("   dim_language[language]  1 -> *  bridge_point_language[language]")
    print("   dim_agency[agency_id]   1 -> *  fact_provision[agency_id]")
    print("   dim_agency[agency_id]   1 -> *  fact_service_point[agency_id]")
    print("   dim_district[district]  1 -> *  fact_gap[district]")
    print("   dim_district[district]  1 -> *  fact_access_desert[district]")
    print("   fact_service_point[location_id] 1 -> * bridge_point_language[location_id]")


MEASURES = r"""// Power BI measures for Language Access in South King County
// Paste each into a new measure. Grouped by what they answer.

// ---------- demand ----------
Families =
SUM ( dim_language[families_total] )

// fact_gap stores every district-language pair TWICE, once per reading.
// A bare SUM therefore double counts: 73,550 against a true 36,775.
// Family counts are identical in both readings (the reading column changes
// how provision is scored, not how many people exist), so either filter is
// correct; filtering is simply how the double count is stopped.
Families in Selection =
CALCULATE ( SUM ( fact_gap[families] ), fact_gap[reading] = "optimistic" )

// ---------- provision ----------
// A tier 3 is a human-translated document. Everything below it is a
// machine widget, a request line, or nothing.
Agencies at Tier 3 =
CALCULATE (
    DISTINCTCOUNT ( fact_provision[agency_id] ),
    fact_provision[written_tier] = 3
)

Best Written Tier =
MAX ( fact_provision[written_tier] )

// The share of tier-3 claims nobody has read. This is the number that
// should be visible on the front page of the report, not buried.
Unverified Tier 3 Share =
VAR Claims =
    CALCULATE ( COUNTROWS ( fact_provision ), fact_provision[written_tier] = 3 )
VAR Verified =
    CALCULATE (
        COUNTROWS ( fact_provision ),
        fact_provision[written_tier] = 3,
        fact_provision[tier_verified] = "verified_human"
    )
RETURN
    DIVIDE ( Claims - Verified, Claims )

// ---------- the gap ----------
// The index is reported two ways. Never show one without the other.
Gap Score (Optimistic) =
CALCULATE ( SUM ( fact_gap[gap_score] ), fact_gap[reading] = "optimistic" )

Gap Score (Conservative) =
CALCULATE ( SUM ( fact_gap[gap_score] ), fact_gap[reading] = "conservative" )

Families With No Written Provision =
CALCULATE (
    SUM ( fact_gap[families_no_written_anywhere] ),
    fact_gap[reading] = "optimistic"
)

Families With No Local Document (Optimistic) =
CALCULATE (
    SUM ( fact_gap[families_no_local_document] ),
    fact_gap[reading] = "optimistic"
)

Families With No Local Document (Conservative) =
CALCULATE (
    SUM ( fact_gap[families_no_local_document] ),
    fact_gap[reading] = "conservative"
)

// DO NOT put this on a card as the headline. It spans 1,760 to 36,611,
// which is 5% to 99.6% of the study population, and a range that wide
// reads as "no idea" rather than "careful". Keep it for a tooltip or an
// appendix, and show the two numbers separately on the page instead.
// See BUILD_GUIDE, Page 1.
No Local Document Range =
VAR Lo = [Families With No Local Document (Optimistic)]
VAR Hi = [Families With No Local Document (Conservative)]
RETURN FORMAT ( Lo, "#,0" ) & " to " & FORMAT ( Hi, "#,0" ) & " families"

// The two facts the range was trying to compress, stated separately.
// One is a measurement; the other is an uncertainty. They are different
// kinds of thing and a single card cannot carry both.
Tier 3 Claims =
CALCULATE ( COUNTROWS ( fact_provision ), fact_provision[written_tier] = 3 )

Tier 3 Claims Verified =
CALCULATE (
    COUNTROWS ( fact_provision ),
    fact_provision[written_tier] = 3,
    fact_provision[tier_verified] = "verified_human"
)

Verification Status =
FORMAT ( [Tier 3 Claims] - [Tier 3 Claims Verified], "#,0" )
    & " of " & FORMAT ( [Tier 3 Claims], "#,0" ) & " never read"

// ---------- access ----------
Service Points =
DISTINCTCOUNT ( fact_service_point[location_id] )

Service Points Serving Language =
DISTINCTCOUNT ( bridge_point_language[location_id] )

Access Deserts =
CALCULATE (
    COUNTROWS ( fact_access_desert ),
    fact_access_desert[is_access_desert] = TRUE ()
)

Families In Access Deserts =
CALCULATE (
    SUM ( fact_access_desert[families] ),
    fact_access_desert[is_access_desert] = TRUE ()
)

// ---------- the ordinance ----------
// KCC 2.15.030.B requires translation into the top six languages "based
// on the County's tier map". The tier map rests on 2016 Census data.
Families Not On KC Tier Map =
CALCULATE ( SUM ( dim_language[families_total] ), dim_language[on_tier_map] = FALSE () )

Families Where Translation Is Required =
CALCULATE ( SUM ( dim_language[families_total] ), dim_language[kc_tier] = 1 )

Families Where Translation Is Optional =
[Families] - [Families Where Translation Is Required]

Share Where Translation Is Optional =
DIVIDE ( [Families Where Translation Is Optional], [Families] )
"""


if __name__ == "__main__":
    main()
