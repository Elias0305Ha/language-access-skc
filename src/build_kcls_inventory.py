"""
Phase 3: build the KCLS rows of the multi-sector supply inventory.

This sector differs from Phase 1 in one important way: the tiers are
DERIVED, not hand-scored. KCLS publishes its language provision as
structured data, so the classification rule can be applied by code
against frozen evidence. Every row therefore carries
assignment_method='derived', and rerunning the script reproduces the
scores exactly. That directly answers known weakness #1, the
single-coder problem, for this sector.

Schema note. Phase 1 rows were keyed (district, language) and carried a
families count, because OSPI reports demand by district. KCLS is one
agency covering many districts, so there is no families count to attach.
Demand joins by geography in Phase 4, not here.

Output: data/inventory/library_inventory.csv
"""

from datetime import date
from pathlib import Path

import pandas as pd

# ---- tuning constants, kept at the top so Phase 4 can sweep them ------

AGENCY_ID = "kcls"
AGENCY_NAME = "King County Library System"
SECTOR = "library"

# Verified by inspection of kcls.org and its library-cards page: there is
# no Google Translate or equivalent widget anywhere on the site.
# Consequence under the classification rule: tier 1 (machine translation)
# is unreachable for this agency, so a language with no in-language
# pathway scores 0, not 1.
HAS_MACHINE_TRANSLATION = False

# Stated on the interpreters page under "Languages that are always
# available". Every other language is described as weekdays only.
ALWAYS_AVAILABLE = {"Chinese-Mandarin", "Russian", "Spanish", "Vietnamese",
                    "American Sign Language"}

# Named explicitly on the interpreters page. ASL has no written form, so
# the section 4 pathway test cannot be applied to it the way it is
# applied to written languages. Scored 2 and flagged. See rule 5.6.
SIGNED_LANGUAGES = {"American Sign Language"}

# collection_tier scale. Tier 1 has no meaning for a physical collection:
# there is no machine-translated book. Documented rather than silently
# skipped.
COLLECTION_ALL_AGES = 3
COLLECTION_CHILDREN_ONLY = 2
COLLECTION_NONE = 0

INTERPRETERS_URL = "https://kcls.org/interpreters/"
COLLECTIONS_URL = "https://kcls.org/collections-by-language-location/"

OUT = Path("data/inventory/library_inventory.csv")


def main():
    today = date.today().isoformat()

    lang_map = pd.read_csv("data/reference/kcls_language_map.csv")
    collections = pd.read_csv("data/processed/kcls_collections.csv")
    locations = pd.read_csv("data/processed/kcls_locations.csv")
    interp_langs = pd.read_csv("data/processed/kcls_interpreter_languages.csv")
    interp_locs = pd.read_csv("data/processed/kcls_interpreter_locations.csv")
    pages = pd.read_csv("data/raw/kcls_translated_pages.csv")
    demand = pd.read_csv("data/processed/demand_by_district.csv")

    study = set(locations[locations["in_study_area"]]["location_name"])
    n_study = len(study)
    n_video = int(interp_locs[interp_locs["in_study_area"]].shape[0])

    # Split the map's mode scope once, so "Chinese serves Cantonese in
    # writing but not in speech" is enforced rather than remembered.
    lang_map["modes"] = lang_map["applies_to_modes"].str.split(",").apply(
        lambda xs: {x.strip() for x in xs})

    def label_english(label):
        """'中文 - Chinese' -> 'Chinese'. Separator is a hyphen or an en dash."""
        for sep in ("–", "—", " - "):
            if sep in label:
                return label.split(sep)[-1].strip()
        return label.strip()

    def canon_for(kcls_english, mode):
        """Canonical languages this KCLS label serves, in this mode."""
        out = []
        for _, r in lang_map.iterrows():
            if label_english(r["kcls_label"]) == kcls_english and mode in r["modes"]:
                out.append(r["canonical_name"])
        return out

    # ---- collections, per canonical language -------------------------
    coll = collections[collections["location_name"].isin(study)
                       & collections["is_physical"]]
    coll_by_lang = {}
    for kcls_en, sub in coll.groupby("language_english"):
        for canon in canon_for(kcls_en, "collection"):
            coll_by_lang[canon] = {
                "branches": sorted(set(sub["location_name"])),
                "children_only": bool(sub["children_only"].all()),
                "kcls_label": kcls_en,
            }

    # ---- in-language request pathway ---------------------------------
    pathway = {}
    for _, r in interp_langs.iterrows():
        for canon in canon_for(r["language_english"], "oral"):
            pathway[canon] = r["evidence_url"]
    for sl in SIGNED_LANGUAGES:
        pathway.setdefault(sl, INTERPRETERS_URL)

    # ---- translated pages --------------------------------------------
    page_by_lang = {}
    for kcls_en, sub in pages.groupby("language"):
        for canon in canon_for(kcls_en, "written"):
            page_by_lang[canon] = sub

    # ---- the language universe ---------------------------------------
    # Union of every language OSPI reports in the study area and every
    # language KCLS serves. The zeros are the finding, so a language with
    # demand and no supply must produce a row, not an absence.
    universe = sorted(set(demand["language"]) | set(lang_map["canonical_name"]))
    print(f"languages in demand: {demand['language'].nunique()}")
    print(f"languages KCLS serves: {lang_map['canonical_name'].nunique()}")
    print(f"inventory rows to build: {len(universe)}")

    unmapped_coll = set(coll["language_english"]) - {
        label_english(x) for x in lang_map["kcls_label"]}
    if unmapped_coll:
        print(f"WARNING collection labels missing from the map: {sorted(unmapped_coll)}")

    rows = []
    for lang in universe:
        c = coll_by_lang.get(lang)
        p = page_by_lang.get(lang)
        has_pathway = lang in pathway

        collection_tier = COLLECTION_NONE
        if c:
            collection_tier = (COLLECTION_CHILDREN_ONLY if c["children_only"]
                               else COLLECTION_ALL_AGES)

        # No widget on this site, so there is no route to tier 1.
        written_tier = 3 if p is not None and len(p) else 0
        assert HAS_MACHINE_TRANSLATION or written_tier != 1

        # Tier 3 oral in Phase 1 meant a named in-language staff member.
        # KCLS publishes no such roster, so 2 is the ceiling on the
        # published evidence. Recorded as a limitation, not as a zero.
        oral_tier = 2 if has_pathway else 0

        notes = []
        if lang in SIGNED_LANGUAGES:
            notes.append("Signed language. Named on the interpreters page as always "
                         "available. The written pathway test in rule 4 does not "
                         "apply as written. See rule 5.6")
        if c and c["children_only"]:
            notes.append("Collection is children's materials only, at "
                         f"{len(c['branches'])} study-area branch(es): "
                         + ", ".join(c["branches"]))
        if c and c["kcls_label"] != lang:
            notes.append(f"KCLS labels this collection '{c['kcls_label']}'")
        if p is not None and len(p):
            verified = int(p["h1_non_latin"].astype(str).str.lower().eq("true").sum())
            notes.append(f"{len(p)} translated page(s); {verified} carry a non-Latin "
                         "heading. Latin-script headings need reading by eye")
            if len(p) == 1 and str(p.iloc[0]["slug"]).startswith("interpreters"):
                notes.append("The only page KCLS publishes in this language is the "
                             "interpreter request page itself")
        if oral_tier == 2 and lang not in ALWAYS_AVAILABLE:
            notes.append("Interpreters weekdays only, per the agency's own FAQ")

        rows.append({
            "agency_id": AGENCY_ID,
            "agency_name": AGENCY_NAME,
            "sector": SECTOR,
            "language": lang,
            "written_tier": written_tier,
            "oral_tier": oral_tier,
            "collection_tier": collection_tier,
            "pathway_in_language": has_pathway,
            "translated_page_count": 0 if p is None else len(p),
            "translated_page_slugs": "" if p is None else "; ".join(p["slug"]),
            "oral_locations_phone": n_study if oral_tier else 0,
            "oral_locations_video": n_video if oral_tier else 0,
            "oral_availability": ("always" if lang in ALWAYS_AVAILABLE
                                  else "weekdays" if oral_tier else ""),
            "collection_branches": 0 if not c else len(c["branches"]),
            "collection_branch_names": "" if not c else "; ".join(c["branches"]),
            "evidence_url": (pathway.get(lang)
                             or (COLLECTIONS_URL if c else INTERPRETERS_URL)),
            "capture_date": today,
            "notes": " | ".join(notes),
            "assigned_by": "EH",
            "assignment_method": "derived",
        })

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"\nwrote {OUT}  ({len(df)} rows)")

    print("\ntier crosstab, written x oral:")
    print(pd.crosstab(df["written_tier"], df["oral_tier"], margins=True))
    print("\ncollection_tier counts:")
    print(df["collection_tier"].value_counts().sort_index().to_string())

    fam = demand.groupby("language")["families"].sum()
    df["families"] = df["language"].map(fam).fillna(0).astype(int)
    top = df.sort_values("families", ascending=False).head(20)
    print("\ntop 20 study-area languages by families:")
    print(top[["language", "families", "written_tier", "oral_tier",
               "collection_tier", "collection_branches"]].to_string(index=False))


if __name__ == "__main__":
    main()
