"""
Phase 3: build the legal aid rows of the supply inventory.

Selection note. Unlike schools or cities there is no fixed roster, so who
counts as a legal aid provider is a judgment. It is recorded in the
AGENCIES list of probe_agency_sites.py: organisations providing free
civil legal help to South King County residents, from an office in the
study area or county/state-wide. Criminal defence is excluded because it
carries its own constitutional interpreter mandate and is not comparable.

The finding this sector produces is structural, and it mirrors the OSPI
multilingual templates in the schools sector:

  WashingtonLawHelp, the statewide legal self-help library run by the
  Northwest Justice Project, publishes substantial human-translated legal
  documents in 13 languages, INCLUDING Dari, Khmer and Marshallese.
  Not one other organisation in this sector publishes in any language
  except Spanish.

  So the material exists, statewide, free, in exactly the languages the
  study area needs and local providers do not offer.

Detection note. This sector broke the detector built for cities. Cities
name a translated page by language slug (…/emergency_information_amharic).
WashingtonLawHelp uses locale path prefixes (…/fa-af/…). Slug detection
alone reported ZERO translated pages at every legal aid organisation,
which was a fact about the detector, not about the sector.

Output: data/inventory/legal_inventory.csv
"""

import json
from datetime import date
from pathlib import Path

import pandas as pd

SECTOR = "legal"
PROFILES = Path("data/raw/agency_site_profiles.json")
SITEMAPS = Path("data/raw/agency_sitemap_urls.json")
GOOGLE = Path("data/raw/google_translate_languages.json")
QUALITY = Path("data/inventory/quality_checks.csv")
OUT = Path("data/inventory/legal_inventory.csv")

# Locale path prefixes -> canonical language. WashingtonLawHelp's own
# codes; fa-af is Dari and fil is Filipino/Tagalog, both of which a bare
# ISO lookup gets wrong.
LOCALE_TO_CANON = {
    "es": "Spanish", "zh-hans": "Chinese-Mandarin", "zh-hant": "Chinese-Cantonese",
    "fa-af": "Dari", "fa": "Farsi", "ar": "Arabic", "ko": "Korean",
    "vi": "Vietnamese", "km": "Khmer", "ru": "Russian", "fil": "Tagalog",
    "mh": "Marshallese", "uk": "Ukrainian", "sgn": "American Sign Language",
    "so": "Somali", "am": "Amharic", "ti": "Tigrinya", "ps": "Pashto",
    "pa": "Punjabi", "ur": "Urdu", "my": "Burmese", "ne": "Nepali",
}

# A locale directory with only a sitemap page in it is not a translation.
MIN_PAGES_FOR_TIER3 = 3

# Findings that are not visible in a sitemap and were read off the page.
# Each carries the URL it came from so a reviewer can check it.
MANUAL = {
    "legal_elap": {
        "in_language_phone": {"Spanish": "425-620-2778"},
        "interpretation_offered": True,
        "evidence": "https://elap.org/get-help/",
        "note": ("Dedicated Spanish help line published beside the English one "
                 "(425-747-7274 English, 425-620-2778 Espanol). Page states "
                 "'ELAP provides free interpretation services'. Help line hours "
                 "Monday to Thursday, 10am to 3:30pm"),
    },
    "legal_nwirp": {
        "translated_docs": {"Spanish": 3},
        "interpretation_offered": True,
        "evidence": "https://nwirp.org/get-help/",
        "note": ("Eligibility requirements published in English and Spanish. "
                 "Of 174 PDFs on the site, 171 are litigation filings; 3 are "
                 "Spanish community materials, dated 2016 and 2020"),
    },
    "legal_nwjustice": {
        "interpretation_offered": True,
        "evidence": "https://nwjustice.org/get-legal-help",
        "note": ("Operates the CLEAR hotline and publishes WashingtonLawHelp, "
                 "which is inventoried as a separate agency because its "
                 "translated library is a distinct service from CLEAR intake"),
    },
}

# Reached no successful response under any header set tried. Recorded as
# unknown rather than zero: "we could not look" and "they provide nothing"
# are different claims and must not collapse into the same row.
UNREACHABLE_NOTE = ("Site returned HTTP 403 to every request. Not assessed. "
                    "Tiers are blank, not zero")


def main():
    today = date.today().isoformat()
    profiles = {p["agency_id"]: p for p in
                json.loads(PROFILES.read_text(encoding="utf-8"))}
    sitemaps = json.loads(SITEMAPS.read_text(encoding="utf-8"))
    google = json.loads(GOOGLE.read_text(encoding="utf-8"))["languages"]
    name_to_code = {v.lower(): k.lower() for k, v in google.items()}

    quality = {}
    if QUALITY.exists():
        for _, r in pd.read_csv(QUALITY).iterrows():
            quality[(r["agency_id"], r["language"])] = r["verdict"]

    demand = pd.read_csv("data/processed/demand_by_district.csv")
    universe = sorted(set(demand["language"]))
    fam = demand.groupby("language")["families"].sum()

    # canonical -> iso, same approach as the city builder
    aliases = {"Farsi": "fa", "Dari": "fa", "Tagalog": "tl", "Burmese": "my",
               "Punjabi": "pa", "Chinese-Mandarin": "zh-cn",
               "Chinese-Cantonese": "zh-tw", "Khmer": "km",
               "American Sign Language": None}
    iso_of = {l: (aliases[l] if l in aliases else name_to_code.get(l.lower()))
              for l in universe}

    legal_ids = [aid for aid, p in profiles.items() if p.get("sector") == "legal"]
    print(f"legal aid agencies: {len(legal_ids)}")

    rows = []
    for aid in legal_ids:
        p = profiles[aid]
        unreachable = bool(p.get("error")) or not p.get("home_status") == 200

        # translated pages, by locale prefix
        by_lang = {}
        for u in sitemaps.get(aid, []):
            parts = u.split("//", 1)[-1].split("/")
            seg = parts[1].lower() if len(parts) > 1 else ""
            canon = LOCALE_TO_CANON.get(seg)
            if canon:
                by_lang.setdefault(canon, []).append(u)
        # ...and by language-named slug, the city pattern, in case both appear
        for slug, us in (p.get("language_named_pages") or {}).items():
            canon = LOCALE_TO_CANON.get(slug) or slug.title()
            if canon in universe:
                by_lang.setdefault(canon, []).extend(us)

        manual = MANUAL.get(aid, {})
        for lang, n in (manual.get("translated_docs") or {}).items():
            by_lang.setdefault(lang, []).extend([manual["evidence"]] * n)

        restricted = p.get("widget_restricted_to")
        restricted_set = {c.strip().lower() for c in restricted} if restricted else None
        has_widget = bool(p.get("widgets"))
        phone = manual.get("in_language_phone", {})
        interp = manual.get("interpretation_offered", False)

        for lang in universe:
            if unreachable:
                rows.append({
                    "agency_id": aid, "agency_name": p["agency_name"],
                    "sector": SECTOR, "language": lang,
                    "written_tier": "", "oral_tier": "", "collection_tier": "",
                    "pathway_in_language": "", "pathway_type": "not_assessed",
                    "translated_page_count": "", "translated_page_slugs": "",
                    "in_language_phone": "", "evidence_url": p["base_url"],
                    "capture_date": today, "quality_verdict": "",
                    "notes": UNREACHABLE_NOTE,
                    "assigned_by": "EH", "assignment_method": "unreachable",
                })
                continue

            iso = iso_of.get(lang)
            if not has_widget or iso is None:
                covered = False
            elif restricted_set is not None:
                covered = iso in restricted_set
            else:
                covered = iso in {c.lower() for c in google}

            pages = by_lang.get(lang, [])
            real = len(pages) >= MIN_PAGES_FOR_TIER3 or lang in phone
            verdict = quality.get((aid, lang), "unchecked" if real else "")

            written = 3 if real else (1 if covered else 0)
            if real and verdict == "machine":
                written = 1                      # rule 5.10

            # Pathway: an in-language phone line is the strongest form,
            # then in-language pages, then a machine widget for discovery.
            if lang in phone:
                ptype = "in_language_phone"
            elif real and verdict != "machine":
                ptype = "in_language_document"
            elif covered and interp:
                ptype = "machine_widget"
            else:
                ptype = "none"
            oral = 2 if (ptype != "none" and interp) else 0

            notes = []
            if pages:
                notes.append(f"{len(pages)} page(s) or document(s) in this language")
                if len(pages) < MIN_PAGES_FOR_TIER3 and lang not in phone:
                    notes.append(f"Below the {MIN_PAGES_FOR_TIER3}-page threshold "
                                 f"for tier 3; a locale directory holding only a "
                                 f"sitemap is not a translation")
            if lang in phone:
                notes.append(f"Dedicated help line published in this language: {phone[lang]}")
            if restricted_set is not None:
                notes.append(f"Widget restricted to {len(restricted_set)} languages; "
                             f"this language is {'on' if covered else 'NOT on'} the list")
            if manual.get("note"):
                notes.append(manual["note"])

            rows.append({
                "agency_id": aid, "agency_name": p["agency_name"],
                "sector": SECTOR, "language": lang,
                "written_tier": written, "oral_tier": oral, "collection_tier": "",
                "pathway_in_language": ptype != "none", "pathway_type": ptype,
                "translated_page_count": len(pages),
                "translated_page_slugs": "; ".join(u.rsplit("/", 1)[-1] for u in pages[:6]),
                "in_language_phone": phone.get(lang, ""),
                "evidence_url": pages[0] if pages else (manual.get("evidence")
                                                        or p.get("final_url", p["base_url"])),
                "capture_date": today, "quality_verdict": verdict,
                "notes": " | ".join(notes),
                "assigned_by": "EH", "assignment_method": "derived",
            })

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"wrote {OUT}  ({len(df)} rows)")

    df["families"] = df["language"].map(fam).fillna(0).astype(int)
    t3 = df[df["written_tier"] == 3]
    print("\nlanguages each organisation publishes in:")
    for org, sub in t3.groupby("agency_name"):
        s = sub.sort_values("families", ascending=False)
        print(f"\n  {org}")
        for r in s.itertuples():
            print(f"      {r.language:22} {r.families:>7,}  {r.translated_page_count} pages")

    print("\nnot assessed:")
    na = df[df["assignment_method"] == "unreachable"]["agency_name"].unique()
    print(f"  {list(na) or 'none'}")


if __name__ == "__main__":
    main()
