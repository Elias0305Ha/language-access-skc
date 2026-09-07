"""
Phase 3: build the health rows of the supply inventory.

Selection note. Included: the safety-net providers a low-income,
limited-English resident of the study area actually uses, plus the state
channels that gate coverage. Excluded: private insurers and specialty
practices, which serve a different population and would dilute the
comparison.

The two findings this sector produces sit at opposite ends.

  BEST IN THE PROJECT. Washington Healthplanfinder, the insurance
  enrollment portal, publishes in 25 languages plus ASL, each with real
  in-language content, a translated PDF and a phone number explained in
  that language. That includes Amharic, Dari, Tigrinya, Oromo, Pashto,
  Punjabi, Khmer, Lao and Somali. Nothing else in this project comes
  close.

  Compare the food sector: DSHS publishes the SNAP application in 12.
  Two state benefit channels, same state, roughly the same clients.

  WORST WIDGET IN THE PROJECT. MultiCare, which operates Auburn Medical
  Center, runs a translation widget configured as
      "languages":["en","es"]
  English and Spanish. Verified in the page source. Auburn is the
  district where Marshallese is 63% of its ACS language bucket.

Output: data/inventory/health_inventory.csv
"""

import json
from datetime import date
from pathlib import Path

import pandas as pd

SECTOR = "health"
PROFILES = Path("data/raw/agency_site_profiles.json")
SITEMAPS = Path("data/raw/agency_sitemap_urls.json")
KC_SITEMAP = Path("data/raw/kingcounty_sitemap_urls.json")
GOOGLE = Path("data/raw/google_translate_languages.json")
QUALITY = Path("data/inventory/quality_checks.csv")
OUT = Path("data/inventory/health_inventory.csv")

PLANFINDER_URL = ("https://www.wahealthplanfinder.org/us/en/tools-and-resources/"
                  "how-to/language-support.html")
PLANFINDER_PHONE = "1-855-923-4633"

# Anchor ids on the Healthplanfinder language support page, each holding
# genuine in-language text, a translated PDF link and the support number
# explained in that language. Verified by reading the anchors.
PLANFINDER_LANGUAGES = {
    "am": "Amharic", "ar": "Arabic", "da": "Dari", "de": "German",
    "fa": "Farsi", "fr": "French", "hi": "Hindi", "ja": "Japanese",
    "km": "Khmer", "ko": "Korean", "lo": "Lao", "om": "Oromo",
    "pa": "Punjabi", "ps": "Pashto", "pt": "Portuguese", "ro": "Romanian",
    "ru": "Russian", "so": "Somali", "ti": "Tigrinya", "tl": "Tagalog",
    "uk": "Ukrainian", "vi": "Vietnamese", "zh-s": "Chinese-Mandarin",
    "zh-t": "Chinese-Cantonese", "es": "Spanish",
    "asl": "American Sign Language",
}

# Public Health Seattle and King County lives under kingcounty.gov, whose
# sitemap is already frozen. Probing it as its own site would report
# 11,587 pages for one department, so its pages are filtered out here.
DPH_PATH = "/dept/dph"
DPH_ID, DPH_NAME = "health_dph", "Public Health Seattle and King County"

# King County's Amharic pages were identified by a native speaker as
# machine output (quality_checks.csv, 2026-09-05). Public Health is a
# King County department publishing through the same CMS, so that verdict
# is INHERITED here rather than re-tested. Marked as inherited, not
# directly checked, so a reviewer can see the difference.
INHERITED_VERDICTS = {("health_dph", "Amharic"): "machine"}

LANGUAGE_SLUGS = [
    "amharic", "arabic", "burmese", "cambodian", "chinese", "chuukese", "dari",
    "farsi", "french", "hindi", "japanese", "khmer", "korean", "lao",
    "marshallese", "nepali", "oromo", "pashto", "persian", "portuguese",
    "punjabi", "romanian", "russian", "samoan", "somali", "spanish",
    "swahili", "tagalog", "thai", "tigrinya", "tongan", "ukrainian",
    "urdu", "vietnamese",
]
SLUG_TO_CANON = {
    "cambodian": "Khmer", "persian": "Farsi", "chinese": "Chinese-Mandarin",
}

UNREACHABLE_NOTE = ("Site did not return a usable response. Not assessed. "
                    "Tiers are blank, not zero")

# A clinic is not a website. Interpreters at the point of care are
# mandated for any provider taking federal funds, and none of that is
# visible online. Recorded on every provider row.
CLINIC_CAVEAT = ("Direct care provider. Federally funded providers must offer "
                 "interpreters at the point of care regardless of what their "
                 "website shows, so a web assessment understates this sector. "
                 "Read the tier as published information, not as bedside "
                 "access")
STATE_CHANNEL = {"health_hca", "health_planfinder", "health_doh"}


def canon_of(slug):
    return SLUG_TO_CANON.get(slug, slug.title())


def main():
    today = date.today().isoformat()
    profiles = {p["agency_id"]: p for p in
                json.loads(PROFILES.read_text(encoding="utf-8"))}
    sitemaps = json.loads(SITEMAPS.read_text(encoding="utf-8"))
    google = json.loads(GOOGLE.read_text(encoding="utf-8"))["languages"]
    google_codes = {c.lower() for c in google}
    name_to_code = {v.lower(): k.lower() for k, v in google.items()}

    quality = dict(INHERITED_VERDICTS)
    if QUALITY.exists():
        for _, r in pd.read_csv(QUALITY).iterrows():
            quality.setdefault((r["agency_id"], r["language"]), r["verdict"])

    demand = pd.read_csv("data/processed/demand_by_district.csv")
    universe = sorted(set(demand["language"]))
    fam = demand.groupby("language")["families"].sum()

    aliases = {"Farsi": "fa", "Dari": "fa", "Tagalog": "tl", "Burmese": "my",
               "Punjabi": "pa", "Chinese-Mandarin": "zh-cn",
               "Chinese-Cantonese": "zh-tw", "Khmer": "km",
               "American Sign Language": None}
    iso_of = {l: (aliases[l] if l in aliases else name_to_code.get(l.lower()))
              for l in universe}

    # Public Health pages, from the frozen King County sitemap
    dph_pages = {}
    for u in json.loads(KC_SITEMAP.read_text(encoding="utf-8")):
        if DPH_PATH not in u:
            continue
        slug = u.rstrip("/").split("/")[-1].lower()
        for L in LANGUAGE_SLUGS:
            if slug == L or slug.endswith("-" + L):
                dph_pages.setdefault(canon_of(L), []).append(u)
                break

    agencies = [aid for aid, p in profiles.items() if p.get("sector") == "health"]
    print(f"health agencies profiled: {len(agencies)}  (+1 for Public Health)")
    print(f"Public Health translated pages: {sum(len(v) for v in dph_pages.values())} "
          f"across {len(dph_pages)} languages")

    rows = []
    for aid in agencies + [DPH_ID]:
        if aid == DPH_ID:
            p = {"agency_id": DPH_ID, "agency_name": DPH_NAME,
                 "base_url": "https://kingcounty.gov/en/dept/dph",
                 "home_status": 200, "widgets": ["google_translate"],
                 "widget_restricted_to": None, "language_access_page_count": 1}
            by_lang = dph_pages
        else:
            p = profiles[aid]
            by_lang = {}
            for slug, us in (p.get("language_named_pages") or {}).items():
                by_lang.setdefault(canon_of(slug), []).extend(us)

        unreachable = bool(p.get("error")) or p.get("home_status") != 200
        restricted = p.get("widget_restricted_to")
        restricted_set = {c.strip().lower() for c in restricted} if restricted else None
        has_widget = bool(p.get("widgets"))
        has_access = p.get("language_access_page_count", 0) > 0
        is_state = aid in STATE_CHANNEL

        for lang in universe:
            if unreachable:
                rows.append({
                    "agency_id": aid, "agency_name": p["agency_name"],
                    "sector": SECTOR, "language": lang,
                    "written_tier": "", "oral_tier": "", "collection_tier": "",
                    "pathway_in_language": "", "pathway_type": "not_assessed",
                    "translated_page_count": "", "translated_page_slugs": "",
                    "widget_language_count": "", "is_state_channel": is_state,
                    "evidence_url": p["base_url"], "capture_date": today,
                    "quality_verdict": "", "notes": UNREACHABLE_NOTE,
                    "assigned_by": "EH", "assignment_method": "unreachable",
                })
                continue

            iso = iso_of.get(lang)
            covered = bool(has_widget and iso and
                           (iso in restricted_set if restricted_set is not None
                            else iso in google_codes))

            pages = by_lang.get(lang, [])
            notes = []

            # Healthplanfinder is scored from its language support page,
            # not from a sitemap: each anchor holds real in-language text.
            if aid == "health_planfinder" and lang in PLANFINDER_LANGUAGES.values():
                pages = [PLANFINDER_URL]
                notes.append(f"In-language section with a translated PDF and the "
                             f"support number {PLANFINDER_PHONE} explained in this "
                             f"language")

            verdict = quality.get((aid, lang), "unchecked" if pages else "")
            written = 3 if pages else (1 if covered else 0)
            if pages and verdict == "machine":
                written = 1
                notes.append("Identified as machine translation, so tier 3 is "
                             "not met. Rule 5.10")
                if (aid, lang) in INHERITED_VERDICTS:
                    notes.append("Verdict INHERITED from the King County check "
                                 "of 2026-09-05, same organisation and CMS. Not "
                                 "independently re-read")

            in_lang_doc = bool(pages) and verdict != "machine"
            ptype = ("in_language_document" if in_lang_doc
                     else "machine_widget" if (covered and has_access) else "none")
            oral = 2 if ptype != "none" else 0

            if restricted_set is not None:
                notes.append(f"Translation widget restricted to "
                             f"{len(restricted_set)} languages; this language is "
                             f"{'on' if covered else 'NOT on'} the list")
            elif has_widget and not pages:
                notes.append("Unrestricted widget, machine translation only")
            elif not has_widget and not pages:
                notes.append("No translation mechanism found on the site")
            if not is_state:
                notes.append(CLINIC_CAVEAT)
            # Limitation 7 made concrete. The one King County language a
            # reader could check turned out to be machine output, so every
            # other King County language carries the same unmeasured risk.
            # Saying so only on the Amharic row would hide it.
            if aid == DPH_ID and pages and verdict != "machine":
                notes.append("King County's Amharic pages were identified as "
                             "machine translation by a native speaker. No other "
                             "King County language could be checked by anyone on "
                             "this project, so this tier 3 is structurally "
                             "detected and UNVERIFIED. See limitation 7")

            rows.append({
                "agency_id": aid, "agency_name": p["agency_name"],
                "sector": SECTOR, "language": lang,
                "written_tier": written, "oral_tier": oral, "collection_tier": "",
                "pathway_in_language": ptype != "none", "pathway_type": ptype,
                "translated_page_count": len(pages),
                "translated_page_slugs": "; ".join(
                    u.rstrip("/").split("/")[-1] for u in pages[:6]),
                "widget_language_count": len(restricted_set) if restricted_set else "",
                "is_state_channel": is_state,
                "evidence_url": pages[0] if pages else p.get("final_url", p["base_url"]),
                "capture_date": today, "quality_verdict": verdict,
                "notes": " | ".join(notes),
                "assigned_by": "EH", "assignment_method": "derived",
            })

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"\nwrote {OUT}  ({len(df)} rows)\n")

    df["families"] = df["language"].map(fam).fillna(0).astype(int)
    t3 = df[df["written_tier"] == 3]
    print("languages each organisation publishes in:")
    for org, sub in t3.groupby("agency_name"):
        s = sub.sort_values("families", ascending=False)
        print(f"\n  {org} ({len(s)})")
        print("     " + ", ".join(f"{r.language}" for r in s.itertuples()))

    print("\n\nwidget language counts, where the widget is restricted:")
    w = df[df["widget_language_count"] != ""].drop_duplicates("agency_name")
    print(w[["agency_name", "widget_language_count"]].to_string(index=False))

    print("\nnot assessed:")
    print(f"  {sorted(set(df[df['assignment_method']=='unreachable']['agency_name'])) or 'none'}")


if __name__ == "__main__":
    main()
