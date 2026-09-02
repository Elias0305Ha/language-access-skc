"""
Phase 1 gap table.

Joins demand (families who prefer a language) to supply (what the district
actually provides) and reports the shortfall three ways.

v2 change. v1 used one shortfall scale for both modes and produced a
nonsense ranking: Auburn Spanish, which has translated documents AND
interpreters, scored 617.8 while Highline Amharic, which has nothing at
all, scored 164.

Two causes, both fixed here:
  1. Oral tier 3 means a named bilingual liaison. No district can staff one
     for 193 languages, so nearly every row sits at oral tier 2 permanently.
     Charging 0.6 for that put an unremovable penalty on every family and
     made the score track population size instead of unmet need.
  2. A single score cannot answer "who is worst" and "who is biggest" at
     once. It now reports three numbers instead of collapsing them.

All weights are constants so the Phase 4 sensitivity analysis can sweep
them without touching the logic.
"""

import pandas as pd
from pathlib import Path

# --- tuning constants -------------------------------------------------
# Fraction of the need still unmet at each tier. 0.0 means fully served.

# Written. The 2-to-3 step is deliberately the largest, per rule 6.6:
# an unrestricted Google Translate widget hands out tier 2 to everyone, so
# tier 2 does not distinguish agencies. Documents that already exist do.
SHORTFALL_WRITTEN = {3: 0.0, 2: 0.60, 1: 0.85, 0: 1.0}

# Oral. A requestable interpreter is the normal adequate provision, and
# for most languages it is the best that realistically exists. Scoring it
# as heavily unmet would penalise districts for the shape of the world.
SHORTFALL_ORAL = {3: 0.0, 2: 0.20, 1: 0.70, 0: 1.0}

W_WRITTEN = 0.7
W_ORAL = 0.3
# ----------------------------------------------------------------------

inv = pd.read_csv("data/inventory/school_inventory.csv")

missing = inv[inv["written_tier"].isna() | inv["oral_tier"].isna()]
if len(missing):
    print("WARNING: unscored rows found, they are excluded:")
    print(missing[["agency_name", "language"]].to_string(index=False))
    inv = inv.dropna(subset=["written_tier", "oral_tier"])

inv["written_tier"] = inv["written_tier"].astype(int)
inv["oral_tier"] = inv["oral_tier"].astype(int)

inv["written_gap"] = inv["families"] * inv["written_tier"].map(SHORTFALL_WRITTEN)
inv["oral_gap"] = inv["families"] * inv["oral_tier"].map(SHORTFALL_ORAL)

# Measure 1: weighted gap. Volume-sensitive, good for "how many people".
inv["gap_score"] = (W_WRITTEN * inv["written_gap"]
                    + W_ORAL * inv["oral_gap"]).round(1)

# Measure 2: severity per family. Population-independent, good for
# "how badly is this served", comparable across districts of any size.
inv["severity"] = (inv["gap_score"] / inv["families"]).round(3)

# Measure 3: the plain count. No weights, no judgment calls, nothing to
# argue with. Families with no written provision in their language at all.
inv["families_unserved"] = (inv["families"]
                            .where(inv["written_tier"] == 0, 0))

gap = inv.sort_values("gap_score", ascending=False)

Path("outputs").mkdir(exist_ok=True)
cols = ["agency_name", "sector", "language", "families",
        "written_tier", "oral_tier", "written_gap", "oral_gap",
        "gap_score", "severity", "families_unserved",
        "evidence_url", "capture_date", "notes"]
gap[cols].to_csv("outputs/gap_index_phase1.csv", index=False)
print("wrote outputs/gap_index_phase1.csv\n")


print("=== 1. FAMILIES WITH NO WRITTEN PROVISION ===")
print("    plain counts, no weighting")
unserved = (gap[gap["written_tier"] == 0]
            .sort_values("families", ascending=False))
print(unserved[["agency_name", "language", "families", "oral_tier"]]
      .to_string(index=False))
print(f"\n    TOTAL: {unserved['families'].sum():,} families")


print("\n\n=== 2. WORST SERVED, by severity per family ===")
print("    size-independent, a small district cannot hide")
sev = gap.sort_values("severity", ascending=False)
print(sev.head(15)[["agency_name", "language", "families",
                    "written_tier", "oral_tier", "severity"]]
      .to_string(index=False))


print("\n\n=== 3. LARGEST WEIGHTED GAPS ===")
print("    volume-sensitive, tracks total families affected")
print(gap.head(15)[["agency_name", "language", "families",
                    "written_tier", "oral_tier", "gap_score"]]
      .to_string(index=False))


print("\n\n=== BY DISTRICT ===")
by_dist = (gap.groupby("agency_name")
           .agg(families=("families", "sum"),
                gap_score=("gap_score", "sum"),
                families_unserved=("families_unserved", "sum"),
                langs_no_documents=("written_tier", lambda s: (s < 3).sum()),
                langs_nothing=("written_tier", lambda s: (s == 0).sum())))
by_dist["severity"] = (by_dist["gap_score"] / by_dist["families"]).round(3)
by_dist = by_dist.sort_values("severity", ascending=False)
print(by_dist.to_string())


print("\n\n=== BY LANGUAGE, summed across districts ===")
by_lang = (gap.groupby("language")
           .agg(families=("families", "sum"),
                gap_score=("gap_score", "sum"),
                families_unserved=("families_unserved", "sum"),
                districts_at_zero=("written_tier", lambda s: (s == 0).sum()))
           .sort_values("districts_at_zero", ascending=False))
print(by_lang[by_lang["districts_at_zero"] > 0].to_string())
