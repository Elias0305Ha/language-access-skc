"""
Phase 3: parse the frozen KCLS interpreters page into the oral-supply facts.

Three distinct claims live on that page and they have different scopes.
Keeping them apart matters, because they answer different tier questions:

  1. PATHWAY. The request page itself is republished in 9 languages.
     This is what your rule 5 actually tests: can a speaker of language X
     discover, in language X, that the service exists?

  2. REACH. Language Line supplies phone interpreting in 240+ languages
     at every branch. Wide, but only reachable if you already know to ask.

  3. DEPTH. Video and audio interpreting exists at a named subset of
     branches only, funded by a Washington State Library grant.

Outputs:
  data/processed/kcls_interpreter_languages.csv   claim 1
  data/processed/kcls_interpreter_locations.csv   claim 3
"""

import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

SRC = Path("data/raw/kcls_interpreters.html")
LOCS = Path("data/processed/kcls_locations.csv")
OUT_LANG = Path("data/processed/kcls_interpreter_languages.csv")
OUT_LOC = Path("data/processed/kcls_interpreter_locations.csv")

# The page links its translations by URL slug. Mapping slug to an English
# language name is a hand judgement, so it is written down here rather
# than inferred, and one of them is wrong at the source. See PASHTO note.
SLUG_TO_LANGUAGE = {
    "es": "Spanish",
    "zh-ch": "Chinese",
    "ru": "Russian",
    "vi": "Vietnamese",
    "so": "Somali",
    "am": "Amharic",
    "ar": "Arabic",
    "pa": "Pashto",     # see below
    "uk": "Ukrainian",
}

# KCLS labels this link پښتو, which is the Pashto endonym. The slug they
# used is "pa", which is the ISO 639-1 code for Punjabi; Pashto is "ps".
# We follow the label, not the slug, because the label is what a reader
# sees and acts on. Flagged so a reviewer can check the linked page.
PASHTO_SLUG_ANOMALY = ("pa", "label says Pashto, slug 'pa' is the ISO code for Punjabi")

# Stated on the page under "Languages that are always available".
# Everything else is described as weekdays-only, which is a real
# restriction and is recorded rather than rounded up to 'available'.
ALWAYS_AVAILABLE = ["American Sign Language (ASL)", "Mandarin", "Russian",
                    "Spanish", "Vietnamese"]


def main():
    soup = BeautifulSoup(SRC.read_text(encoding="utf-8"), "lxml")
    text = soup.get_text("\n", strip=True)

    # ---- claim 1: which languages the request page itself exists in ----
    rows, seen = [], set()
    for a in soup.select('a[href*="interpreters-"]'):
        slug = a["href"].rstrip("/").split("interpreters-")[-1]
        if slug in seen:
            continue
        seen.add(slug)
        rows.append({
            "agency_id": "kcls",
            "language_english": SLUG_TO_LANGUAGE.get(slug),
            "language_native": a.get_text(" ", strip=True),
            "pathway_in_language": True,
            "evidence_url": a["href"],
            "slug": slug,
        })

    langs = pd.DataFrame(rows)
    unmapped = langs[langs["language_english"].isna()]["slug"].tolist()
    print(f"in-language request pages: {len(langs)}")
    if unmapped:
        print(f"WARNING unmapped slugs, add to SLUG_TO_LANGUAGE: {unmapped}")
    print(langs[["language_english", "language_native", "slug"]].to_string(index=False))
    print(f"\nSOURCE ANOMALY: slug '{PASHTO_SLUG_ANOMALY[0]}', {PASHTO_SLUG_ANOMALY[1]}")

    # ---- claim 3: which branches have video/audio interpreting --------
    m = re.search(r"available at these locations:\n(.*?)\nWhy aren", text, re.S)
    if not m:
        raise SystemExit("could not find the video/audio location list; page layout changed")
    names = [n.strip() for n in m.group(1).split("\n") if n.strip()]
    print(f"\nbranches with video/audio interpreting: {len(names)}")

    locs = pd.read_csv(LOCS)
    known = set(locs["location_name"])
    matched = [n for n in names if n in known]
    unmatched = [n for n in names if n not in known]
    if unmatched:
        # Do not quietly drop. 'Service Center' is the admin office,
        # listed under a shorter name than the locations API uses.
        print(f"UNMATCHED against locations table: {unmatched}")

    loc_df = pd.DataFrame({"location_name": names})
    loc_df["agency_id"] = "kcls"
    loc_df["video_audio_interpreting"] = True
    loc_df = loc_df.merge(
        locs[["location_name", "district_name", "in_study_area", "location_type"]],
        on="location_name", how="left",
    )
    loc_df["in_study_area"] = loc_df["in_study_area"].fillna(False)

    in_study = loc_df[loc_df["in_study_area"]]
    print(f"of which inside the study area: {len(in_study)} of "
          f"{int(locs['in_study_area'].sum())} study-area locations")
    print(in_study.groupby("district_name")["location_name"].count().to_string())

    # Which study-area branches are NOT on the list. This is the finding,
    # phone-only branches are a lesser service.
    missing = set(locs[locs["in_study_area"]]["location_name"]) - set(names)
    print(f"\nstudy-area locations WITHOUT video/audio interpreting: {sorted(missing)}")

    print(f"\nalways-available languages (all other languages are weekdays only):")
    for x in ALWAYS_AVAILABLE:
        print(f"  {x}")

    OUT_LANG.parent.mkdir(parents=True, exist_ok=True)
    langs.to_csv(OUT_LANG, index=False)
    loc_df.to_csv(OUT_LOC, index=False)
    print(f"\nwrote {OUT_LANG}  ({len(langs)} rows)")
    print(f"wrote {OUT_LOC}  ({len(loc_df)} rows)")


if __name__ == "__main__":
    main()
