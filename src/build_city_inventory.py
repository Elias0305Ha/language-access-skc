"""
Phase 3: build the city-government rows of the supply inventory.

Eight cities, scored from the frozen site profiles in
data/raw/agency_site_profiles.json.

The scoring logic, stated before the code so it can be argued with:

  written_tier
    3  the city publishes a page in this language
       (detected as a language-named slug in its own sitemap)
    1  no such page, but the city's translation widget covers the language
    0  neither

  oral_tier
    2  the widget covers this language AND the city publishes at least one
       language-access page for a speaker to discover
    0  otherwise

    The second condition matters. A widget that can translate a page is
    only a pathway if there is something on the page to find. A city with
    no interpreter offer anywhere on its site has nothing for the widget
    to make discoverable, so the widget alone does not earn tier 2.
    Des Moines is the case: 196 pages, no language-access page at all.

  Three cities restrict their widget to an explicit list. For those, a
  language counts as covered only if it is on the list. For the rest the
  widget is unrestricted and coverage is the full Google set, so the
  binding constraint is what Google supports, not what the city chose.

Output: data/inventory/city_inventory.csv
"""

import json
from datetime import date
from pathlib import Path

import pandas as pd

SECTOR = "city"
PROFILES = Path("data/raw/agency_site_profiles.json")
GOOGLE = Path("data/raw/google_translate_languages.json")
OUT = Path("data/inventory/city_inventory.csv")
QUALITY = Path("data/inventory/quality_checks.csv")

# Canonical study-area name -> ISO code as the widgets write it.
# Built by hand because the widgets use bare ISO codes and the demand
# table uses names, and a wrong entry here silently changes a tier.
CANON_TO_ISO = {
    "Spanish": "es", "Vietnamese": "vi", "Somali": "so", "Amharic": "am",
    "Ukrainian": "uk", "Russian": "ru", "Arabic": "ar", "Tagalog": "tl",
    "Korean": "ko", "Punjabi": "pa", "Nepali": "ne", "Burmese": "my",
    "French": "fr", "Portuguese": "pt", "Hindi": "hi", "Japanese": "ja",
    "Khmer": "km", "Thai": "th", "Turkish": "tr", "Swahili": "sw",
    "Urdu": "ur", "Romanian": "ro", "Lao": "lo", "Samoan": "sm",
    "Tongan": "to", "Oromo": "om", "Tigrinya": "ti", "Marshallese": "mh",
    "Chuukese": "chk", "Pashto": "ps", "Hebrew": "he", "German": "de",
    "Italian": "it", "Chinese-Mandarin": "zh-CN", "Chinese-Cantonese": "zh-TW",
    # Farsi and Dari share a written standard. A site offering "fa" is
    # offering text a Dari reader can read, which is the same call already
    # made for the library sector. Recorded here rather than assumed.
    "Farsi": "fa", "Dari": "fa",
    "Haitian Creole": "ht", "Kurdish": "ku", "Bengali": "bn",
    "Indonesian": "id", "Ilokano": "ilo", "Mien": None, "Karen": None,
    "Kosraean": None, "American Sign Language": None,
}

# Two cities publish translated pages under a language-named slug but
# their sitemap slug differs from the canonical name.
SLUG_TO_CANON = {
    "spanish": "Spanish", "vietnamese": "Vietnamese", "somali": "Somali",
    "amharic": "Amharic", "ukrainian": "Ukrainian", "dari": "Dari",
    "burmese": "Burmese", "nepali": "Nepali", "russian": "Russian",
    "arabic": "Arabic", "korean": "Korean", "chinese": "Chinese-Mandarin",
    "tagalog": "Tagalog", "punjabi": "Punjabi", "khmer": "Khmer",
    "french": "French", "tigrinya": "Tigrinya", "oromo": "Oromo",
    "pashto": "Pashto", "farsi": "Farsi", "persian": "Farsi",
    "marshallese": "Marshallese", "portuguese": "Portuguese",
    "thai": "Thai", "hindi": "Hindi", "japanese": "Japanese",
    "samoan": "Samoan", "swahili": "Swahili", "urdu": "Urdu",
    "turkish": "Turkish", "lao": "Lao", "tongan": "Tongan",
    "romanian": "Romanian", "chuukese": "Chuukese", "hmong": "Hmong",
    "cambodian": "Khmer", "ilocano": "Ilokano", "mien": "Mien",
    "karen": "Karen", "german": "German", "italian": "Italian",
}


def main():
    today = date.today().isoformat()
    profiles = json.loads(PROFILES.read_text(encoding="utf-8"))
    google = json.loads(GOOGLE.read_text(encoding="utf-8"))["languages"]
    google_codes = {c.lower() for c in google}

    # Native-speaker quality verdicts. Recorded, never used to change a
    # tier: see CLASSIFICATION_RULE 5.10 for why downgrading only the
    # language we can read would bias the dataset against that language.
    quality = {}
    if QUALITY.exists():
        q = pd.read_csv(QUALITY)
        for _, r in q.iterrows():
            quality[(r["agency_id"], r["language"])] = r["verdict"]
        print(f"quality checks on file: {len(quality)}")

    demand = pd.read_csv("data/processed/demand_by_district.csv")
    universe = sorted(set(demand["language"]))
    fam = demand.groupby("language")["families"].sum()

    # Derive the code from Google's own name list wherever the names agree.
    # Hand-typing all 138 produced 93 "unmapped" languages, several of
    # which (Albanian, Armenian, Bosnian, Bulgarian, Cebuano) Google
    # plainly supports. That is a lookup gap masquerading as a finding.
    # CANON_TO_ISO now holds only the genuine judgment calls and aliases.
    name_to_code = {v.lower(): k for k, v in google.items()}
    iso_of = {}
    for lang in universe:
        if lang in CANON_TO_ISO:
            iso_of[lang] = CANON_TO_ISO[lang]
        else:
            iso_of[lang] = name_to_code.get(lang.lower())

    unmapped = [l for l in universe if not iso_of[l]]
    print(f"study-area languages: {len(universe)}")
    print(f"resolved to an ISO code: {len(universe) - len(unmapped)}")
    print(f"no code, no widget can cover them, scored 0: {len(unmapped)}")
    print(f"  {sorted(unmapped)[:20]}")

    rows = []
    for p in profiles:
        if p.get("error"):
            print(f"SKIPPED {p['agency_name']}: {p['error']}")
            continue

        restricted = p.get("widget_restricted_to")
        restricted_set = {c.strip().lower() for c in restricted} if restricted else None
        has_widget = bool(p.get("widgets"))
        has_access_page = p.get("language_access_page_count", 0) > 0

        # sitemap slug -> canonical name, for this city's translated pages
        translated = {}
        for slug, urls in (p.get("language_named_pages") or {}).items():
            canon = SLUG_TO_CANON.get(slug)
            if canon:
                translated.setdefault(canon, []).extend(urls)

        for lang in universe:
            iso = iso_of.get(lang)
            if not has_widget or iso is None:
                covered = False
            elif restricted_set is not None:
                covered = iso.lower() in restricted_set
            else:
                covered = iso.lower() in google_codes

            pages = translated.get(lang, [])
            written = 3 if pages else (1 if covered else 0)
            oral = 2 if (covered and has_access_page) else 0

            notes = []
            if pages:
                notes.append(f"{len(pages)} page(s) published in this language")
            if restricted_set is not None:
                notes.append(f"Widget restricted to {len(restricted_set)} languages; "
                             f"this language is {'on' if covered else 'NOT on'} the list")
            elif has_widget and covered:
                notes.append("Unrestricted widget, machine translation only")
            elif has_widget and not covered:
                notes.append("Widget present but does not support this language")
            else:
                notes.append("No translation mechanism found on the site")
            if not has_access_page:
                notes.append("City publishes no language-access or interpreter page, "
                             "so there is nothing for a speaker to discover")

            rows.append({
                "agency_id": p["agency_id"], "agency_name": p["agency_name"],
                "sector": SECTOR, "language": lang,
                "written_tier": written, "oral_tier": oral, "collection_tier": "",
                "pathway_in_language": covered and has_access_page,
                "pathway_type": ("in_language_document" if pages
                                 else "machine_widget" if (covered and has_access_page)
                                 else "none"),
                "widget": ",".join(p.get("widgets") or []),
                "widget_restricted": restricted_set is not None,
                "widget_language_count": len(restricted_set) if restricted_set else "",
                "translated_page_count": len(pages),
                "translated_page_slugs": "; ".join(u.rstrip("/").split("/")[-1] for u in pages),
                "language_access_page_count": p.get("language_access_page_count", 0),
                "site_page_count": p.get("sitemap_page_count", 0),
                "evidence_url": pages[0] if pages else p.get("final_url", p["base_url"]),
                "capture_date": today,
                "quality_verdict": quality.get((p["agency_id"], lang),
                                               "unchecked" if pages else ""),
                "notes": " | ".join(notes),
                "assigned_by": "EH", "assignment_method": "derived",
            })

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"\nwrote {OUT}  ({len(df)} rows)")

    df["families"] = df["language"].map(fam).fillna(0).astype(int)

    print("\nfamilies reached, by city and pathway type:")
    piv = df.pivot_table(index="agency_name", columns="pathway_type",
                         values="families", aggfunc="sum", fill_value=0)
    for c in ["in_language_document", "machine_widget", "none"]:
        if c not in piv:
            piv[c] = 0
    print(piv[["in_language_document", "machine_widget", "none"]].to_string())

    print("\nlanguages each city publishes a page in:")
    t3 = df[df["written_tier"] == 3]
    for city, sub in t3.groupby("agency_name"):
        langs = sub.sort_values("families", ascending=False)
        print(f"  {city}: " + ", ".join(f"{r.language} ({r.families:,})"
                                        for r in langs.itertuples()))


if __name__ == "__main__":
    main()
