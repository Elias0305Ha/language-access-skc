"""
Phase 4: sensitivity analysis for the gap index.

Why this exists. The index rests on weights chosen by one analyst: how
much a statewide resource counts against a district one, how heavily an
unverified tier 3 is discounted, how written provision trades off against
oral. A reviewer is entitled to ask whether the ranking is a finding or
an artefact of those choices.

This sweeps them and reports two things:

  1. How far the headline numbers move. If "families with no local
     document" swings from 1,000 to 30,000 depending on a weight, the
     number needs a range, not a point estimate.

  2. Whether the ORDER changes. Spearman rank correlation of the
     language ranking against the baseline. A finding that survives every
     reasonable weighting is robust; one that only appears under a
     particular setting is not a finding.

Scenarios are deliberately chosen to include settings that would WEAKEN
the project's conclusions, not just ones that flatter them.

RESULT, recorded here so it is not buried in a CSV.

The ranking is robust to every scenario except one.

  Stable: the 393 families with no written provision anywhere move only
  between 376 and 393 across all 11 scenarios. Rank correlation with the
  baseline is 1.000 in six scenarios and above 0.95 in nine of eleven.
  Spanish is the worst-served language in ten of eleven. Flattening the
  scope weights entirely, which would erase design decision 1, does not
  change the ranking at all.

  NOT stable: "written_only" (oral provision given zero weight) gives a
  rank correlation of 0.266 and shares only 3 of the baseline top 10.
  The cause is explainable rather than alarming. Most languages sit at
  oral tier 2 because an unrestricted widget satisfies the discovery
  pathway, so the oral term is close to uniform across languages. Remove
  it and small languages with no written provision at all dominate; the
  worst language becomes Turkish (161 families) rather than Spanish
  (19,569).

  Whether that matters depends on the question. "Which language is worst
  served per family" and "where is the largest unmet need" are different
  questions, and the index answers the second. It is reported here rather
  than smoothed over.

Output: outputs/sensitivity_analysis.csv
"""

import copy
from pathlib import Path

import pandas as pd

from build_gap_index import DEFAULT_PARAMS, load_inputs, compute_index

OUT = Path("outputs/sensitivity_analysis.csv")


def variant(**overrides):
    p = copy.deepcopy(DEFAULT_PARAMS)
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(p.get(k), dict):
            p[k] = {**p[k], **v}
        else:
            p[k] = v
    return p


SCENARIOS = {
    "baseline": DEFAULT_PARAMS,

    # Distance of authority. The flat case is the strongest challenge:
    # it says a statewide website counts exactly as much as the district
    # that sends your child's letter, which would erase decision 1.
    "scope_flat_all_equal": variant(scope_weight={
        "district": 1.0, "city": 1.0, "county": 1.0, "regional": 1.0, "state": 1.0}),
    "scope_steep_local_only": variant(scope_weight={
        "district": 1.0, "city": 0.8, "county": 0.4, "regional": 0.2, "state": 0.1}),

    # Verification. Trusting every claim is the reading most favourable
    # to the agencies; assuming machine is the harshest.
    "trust_all_tier3": variant(unverified_tier3_as=3),
    "assume_unverified_is_machine": variant(unverified_tier3_as=1),

    # Mode weighting.
    "written_and_oral_equal": variant(w_written=0.5, w_oral=0.5),
    "written_only": variant(w_written=1.0, w_oral=0.0),
    "oral_weighted_heavier": variant(w_written=0.5, w_oral=0.5,
                                     shortfall_oral={3: 0.0, 2: 0.5, 1: 0.85, 0: 1.0}),

    # Tier 2 is nearly free for any agency running an unrestricted
    # widget. This tests whether treating it as adequate changes anything.
    "tier2_counted_as_adequate": variant(
        shortfall_written={3: 0.0, 2: 0.20, 1: 0.85, 0: 1.0}),

    # City-district overlap threshold.
    "city_overlap_any": variant(min_city_overlap_pct=0.0),
    "city_overlap_strict_25pct": variant(min_city_overlap_pct=25.0),
}


def main():
    _, assessed, overlap, demand = load_inputs()

    base = None
    rows = []
    for name, params in SCENARIOS.items():
        g = compute_index(assessed, overlap, demand, params)
        opt = g[g["reading"] == "optimistic"]
        con = g[g["reading"] == "conservative"]

        ranking = (opt.groupby("language")["gap_score"].sum()
                   .sort_values(ascending=False))
        if base is None:
            base = ranking
            rho, top10_kept = 1.0, 10
        else:
            joined = pd.concat([base.rank(ascending=False),
                                ranking.rank(ascending=False)], axis=1).dropna()
            # Both columns are already ranks, so Pearson on ranks IS
            # Spearman. Avoids a scipy dependency for one number.
            rho = joined.iloc[:, 0].corr(joined.iloc[:, 1], method="pearson")
            top10_kept = len(set(base.head(10).index) & set(ranking.head(10).index))

        rows.append({
            "scenario": name,
            "no_written_anywhere": int(opt["families_no_written_anywhere"].sum()),
            "no_local_document_optimistic": int(opt["families_no_local_document"].sum()),
            "no_local_document_conservative": int(con["families_no_local_document"].sum()),
            "total_gap_score_optimistic": round(opt["gap_score"].sum(), 1),
            "worst_language": ranking.index[0],
            "second_worst": ranking.index[1],
            "rank_corr_vs_baseline": round(rho, 3),
            "top10_languages_shared_with_baseline": top10_kept,
        })
        print(f"{name:32} worst={ranking.index[0]:<12} "
              f"rho={rho:>5.3f}  top10 kept={top10_kept}/10")

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"\nwrote {OUT}")

    print("\n=== HEADLINE STABILITY ===")
    print(df[["scenario", "no_written_anywhere",
              "no_local_document_optimistic",
              "no_local_document_conservative"]].to_string(index=False))

    print("\n=== RANK STABILITY ===")
    print(df[["scenario", "worst_language", "rank_corr_vs_baseline",
              "top10_languages_shared_with_baseline"]].to_string(index=False))

    print("\nreading:")
    a = df["no_written_anywhere"]
    print(f"  'no written provision anywhere' ranges {a.min():,} to {a.max():,} "
          f"across {len(df)} scenarios")
    r = df["rank_corr_vs_baseline"]
    print(f"  rank correlation with baseline ranges {r.min():.3f} to {r.max():.3f}")
    t = df["top10_languages_shared_with_baseline"]
    print(f"  worst-10 languages shared with baseline: {t.min()} to {t.max()} of 10")


if __name__ == "__main__":
    main()
