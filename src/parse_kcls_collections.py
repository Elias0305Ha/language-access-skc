"""
Phase 3: parse KCLS world-language collections into a location x language table.

The frozen page states the same facts twice:
  view A, "Language Collections"             -> per language, which branches
  view B, "Language Collections by Location" -> per branch, which languages

View A is authoritative here because each branch is an <a href> to a real
location page, so we get an ID, not a name we have to match. View B is
free text. We parse both anyway and diff them. If KCLS contradicts
itself, that is a finding about the source, and we want it printed rather
than averaged away.

Output: data/processed/kcls_collections.csv
"""

import re
import unicodedata
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

SRC = Path("data/raw/kcls_collections_by_language.html")
LOCS = Path("data/processed/kcls_locations.csv")
OUT = Path("data/processed/kcls_collections.csv")
DIFFS = Path("outputs/kcls_source_disagreements.csv")

# The label separator is sometimes a hyphen, sometimes an en dash.
# Matching only "-" silently loses most of the list.
LABEL_SPLIT = re.compile(r"\s+[-–—]\s+")


def slugify(name):
    """'Federal Way 320th' -> 'federal-way-320th', to match the URL slugs."""
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    n = re.sub(r"[^a-zA-Z0-9]+", "-", n).strip("-").lower()
    return n


def slug_from_href(href):
    """Reduce either KCLS link scheme to one slug.

    25 of the 26 language blocks link like
        kcls.org/locations/auburn/
    The Russian block alone links like
        www.kcls.org/about-us/locations/auburn-library
    Different host, different path, extra suffix. Reading only the last
    path segment therefore matched nothing for Russian, and Russian
    disappeared from the output with no error. Strip the suffix.
    """
    slug = href.rstrip("/").split("/")[-1].lower()
    return re.sub(r"-library$", "", slug)


# Not a building. KCLS Outreach is mobile/deposit service with no address,
# so it is absent from the locations API. Named here so it lands in the
# output as a known non-physical service instead of a silent NaN.
NON_PHYSICAL = {"outreach": "Outreach"}  # label must match view B exactly


def canonical_language(label):
    """For cross-view comparison only. Never written to the output.

    View A writes "Tagalog / Filipino" and "Punjabi/Panjabi".
    View B writes "Tagalog Filipino" and "Punjabi".
    Comparing raw strings reports a difference that is not one.
    """
    m = re.match(r"[A-Za-z]+", label.strip())
    return m.group(0).lower() if m else label.strip().lower()


def main():
    soup = BeautifulSoup(SRC.read_text(encoding="utf-8"), "lxml")

    # ---- 1. split the page into its two views ------------------------
    # A single select() returns nodes in document order, so hitting the
    # "by location" heading flips us from view A to view B. This is
    # sturdier than pattern-matching labels, which is what broke an
    # earlier attempt (it lost Punjabi and Tagalog).
    view = "language"
    lang_items, loc_items = [], []
    for node in soup.select("#languagelocations, .fl-accordion-item"):
        if node.get("id") == "languagelocations":
            view = "location"
            continue
        (lang_items if view == "language" else loc_items).append(node)

    print(f"view A, language accordions: {len(lang_items)}")
    print(f"view B, location accordions: {len(loc_items)}")

    # ---- 2. the location vocabulary ---------------------------------
    # Built from the frozen locations JSON, not typed by hand, so the two
    # KCLS sources are forced to agree on what a branch is called.
    locs = pd.read_csv(LOCS)
    slug_to_loc = {slugify(n): n for n in locs["location_name"]}
    known_names = set(locs["location_name"])

    # ---- 3. parse view A --------------------------------------------
    rows = []
    unlinked = []          # branch mentioned in prose but with no link
    for item in lang_items:
        label = item.select_one(".fl-accordion-button-label").get_text(" ", strip=True)
        parts = LABEL_SPLIT.split(label, maxsplit=1)
        native = parts[0].strip()
        english = parts[1].strip() if len(parts) > 1 else label.strip()

        content = item.select_one(".fl-accordion-content")
        text = content.get_text(" ", strip=True)

        # Whole-collection caveat, e.g. "Children's materials only."
        children_only = bool(re.search(r"children.{0,3}s materials only", text, re.I))

        anchors = content.select('a[href*="/locations/"]')
        slugs = [slug_from_href(a["href"]) for a in anchors]

        # A branch named in the sentence but not hyperlinked would vanish
        # if we only read hrefs. "Outreach (children's only)" is one.
        # Strip the anchor text out and see what place names remain.
        prose = text
        for a in anchors:
            prose = prose.replace(a.get_text(" ", strip=True), " ")
        for cand in re.findall(r"\b[A-Z][a-zA-Z]+(?: [A-Z0-9][a-zA-Z0-9]*)*", prose):
            if cand in known_names or cand == "Outreach":
                unlinked.append((english, cand))

        for slug, anchor in zip(slugs, anchors):
            name = slug_to_loc.get(slug) or NON_PHYSICAL.get(slug)
            rows.append({
                "agency_id": "kcls",
                "language_native": native,
                "language_english": english,
                "location_slug": slug,
                "location_name": name,          # None means slug not recognised
                "is_physical": slug not in NON_PHYSICAL,
                "children_only": children_only,
                "evidence_url": anchor["href"],
                "source_view": "by_language",
            })

    df = pd.DataFrame(rows)
    print(f"\nlanguage x location pairs: {len(df)}")
    print(f"distinct languages:        {df['language_english'].nunique()}")

    unmatched = df[df["location_name"].isna()]["location_slug"].unique()
    if len(unmatched):
        print(f"EXCLUDED slugs with no matching location: {sorted(unmatched)}")
    if unlinked:
        print(f"mentioned in prose but not hyperlinked: {sorted(set(unlinked))}")

    # ---- 4. parse view B and diff ------------------------------------
    b = {}
    for item in loc_items:
        name = item.select_one(".fl-accordion-button-label").get_text(" ", strip=True)
        text = item.select_one(".fl-accordion-content").get_text(" ", strip=True)
        m = re.search(r"available in (.+?)\.\s*(?:Learn more|$)", text, re.I | re.S)
        if not m:
            continue
        langs = set()
        for chunk in re.split(r",|\band\b", m.group(1)):
            chunk = re.sub(r"\(.*?\)", "", chunk).strip(" .’'s")
            if chunk:
                langs.add(chunk)
        b[name] = langs

    a = df.dropna(subset=["location_name"]).groupby("location_name")["language_english"].apply(set).to_dict()

    print("\ncross-check, view A against view B:")
    disagree = 0
    diff_rows = []
    for name in sorted(set(a) | set(b)):
        sa, sb = a.get(name, set()), b.get(name, set())
        # Normalise the two label styles before comparing, e.g.
        # "Punjabi/Panjabi" in A is written "Punjabi" in B.
        na = {canonical_language(x) for x in sa}
        nb = {canonical_language(x) for x in sb}
        if na != nb:
            disagree += 1
            print(f"  {name}:  only in A {sorted(na - nb)}   only in B {sorted(nb - na)}")
            for lang in sorted(na - nb):
                diff_rows.append({"location_name": name, "language": lang,
                                  "claimed_by": "by_language", "missing_from": "by_location"})
            for lang in sorted(nb - na):
                diff_rows.append({"location_name": name, "language": lang,
                                  "claimed_by": "by_location", "missing_from": "by_language"})
    print(f"  locations compared: {len(set(a) | set(b))}, disagreements: {disagree}")

    # Persist, do not only print. These are contradictions inside the
    # source itself, they belong in the published record next to the data.
    DIFFS.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(diff_rows).to_csv(DIFFS, index=False)
    print(f"  wrote {DIFFS}  ({len(diff_rows)} rows)")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"\nwrote {OUT}  ({len(df)} rows)")

    # ---- study-area summary ------------------------------------------
    study = set(locs[locs["in_study_area"]]["location_name"])
    s = df[df["location_name"].isin(study) & df["is_physical"]]
    print(f"\npairs inside the study area: {len(s)}")
    print("\nlanguages by number of study-area branches holding them:")
    print(s.groupby("language_english")["location_name"].nunique()
           .sort_values(ascending=False).to_string())


if __name__ == "__main__":
    main()
