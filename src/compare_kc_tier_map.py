"""
Phase 4: compare King County's own language tier map against measured
demand in the study area.

Why this is the memo's central exhibit.

King County Code 2.15.030.B requires every County agency to hold a
Language Assistance Plan identifying which vital documents must be
translated into "the County's top six languages, based on the County's
tier map." The tier map is therefore the ordinance's own benchmark: the
standard King County set for itself.

The tier map is Appendix C of policy INF-14-2-AEO, headed:

    Language-Rank-Tiers-2016Updt-Final.xlsx
    King County's Top Languages Ranked into Three Tiers
    2016 Census Update Data (Most current as of October 2018)

  Tier 1, translation REQUIRED:     Spanish, and only Spanish
  Tier 2, translation recommended:  8 languages
  Tier 3, translation encouraged:   11 languages

Two structural problems follow, and both are checkable rather than
rhetorical:

  1. The benchmark rests on 2016 Census data. The Afghan evacuation was
     August 2021 and the full-scale invasion of Ukraine was February
     2022. Any language whose local population arrived after 2016
     cannot appear on it.

  2. Only Spanish is required. Every other language is "recommended" or
     "encouraged", which is to say optional.

Output: outputs/kc_tier_map_vs_demand.csv
"""

from pathlib import Path

import pandas as pd

SOURCE = ("https://cdn.kingcounty.gov/-/media/king-county/depts/executive-services/"
          "policies/documents/inf-14-2-aeo-appendix-c.pdf")
SOURCE_TITLE = ("Appendix C: Language Tiers, policy INF-14-2-AEO. "
                "Language-Rank-Tiers-2016Updt-Final.xlsx, "
                "2016 Census Update Data, most current as of October 2018")

# Transcribed from the PDF. Names are King County's own spellings.
TIER_1 = ["Spanish"]
TIER_2 = ["Vietnamese", "Somali", "Russian", "Chinese", "Korean",
          "Amharic", "Arabic", "Ukrainian"]
TIER_3 = ["Tagalog", "Punjabi", "Tigrinya", "Burmese", "Nepali",
          "Cambodian", "Farsi", "Japanese", "Hindi", "Oromo", "Samoan"]

# King County's names to this project's canonical names.
KC_TO_CANON = {
    "Chinese": ["Chinese-Mandarin", "Chinese-Cantonese"],
    "Cambodian": ["Khmer"],
}

OUT = Path("outputs/kc_tier_map_vs_demand.csv")
TOP_N = 25


def build_lookup():
    tier = {}
    for names, t in ((TIER_1, 1), (TIER_2, 2), (TIER_3, 3)):
        for n in names:
            for canon in KC_TO_CANON.get(n, [n]):
                tier[canon] = t
    return tier


def main():
    tier = build_lookup()
    demand = pd.read_csv("data/processed/demand_by_district.csv")
    fam = demand.groupby("language")["families"].sum().sort_values(ascending=False)

    print(SOURCE_TITLE)
    print(f"languages on the tier map: {len(tier)}")
    print(f"  tier 1, REQUIRED:    {TIER_1}")
    print(f"  tier 2, recommended: {len(TIER_2)}")
    print(f"  tier 3, encouraged:  {len(TIER_3)}\n")

    rows = []
    for lang, n in fam.items():
        t = tier.get(lang)
        rows.append({
            "language": lang,
            "families_south_king_county": int(n),
            "kc_tier": t if t else "",
            "kc_status": {1: "translation REQUIRED",
                          2: "translation recommended",
                          3: "translation encouraged"}.get(t, "NOT ON THE TIER MAP"),
            "on_tier_map": bool(t),
            "tier_map_source": SOURCE,
            "tier_map_vintage": "2016 Census data, current as of October 2018",
        })
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    top = df.head(TOP_N)
    print(f"{'language':22}{'families':>10}   King County status")
    for r in top.itertuples():
        mark = "" if r.on_tier_map else "   <=="
        print(f"{r.language:22}{r.families_south_king_county:>10,}   {r.kc_status}{mark}")

    absent = df[~df["on_tier_map"] & (df["families_south_king_county"] > 0)]
    print(f"\nlanguages with measured demand and NO place on the tier map: {len(absent)}")
    print(f"families in them: {absent['families_south_king_county'].sum():,}")
    print("\nlargest absences:")
    for r in absent.head(8).itertuples():
        print(f"   {r.language:22}{r.families_south_king_county:>8,}")

    covered = df[df["on_tier_map"]]["families_south_king_county"].sum()
    total = df["families_south_king_county"].sum()
    req = df[df["kc_tier"] == 1]["families_south_king_county"].sum()
    print(f"\nfamilies whose language is on the tier map at all: "
          f"{covered:,} of {total:,}  ({100*covered/total:.1f}%)")
    print(f"families whose language is tier 1, the only tier where "
          f"translation is REQUIRED: {req:,}  ({100*req/total:.1f}%)")
    print(f"families whose language is merely recommended, encouraged, "
          f"or absent: {total-req:,}  ({100*(total-req)/total:.1f}%)")

    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
