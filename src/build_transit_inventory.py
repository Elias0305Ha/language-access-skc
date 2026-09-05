"""
Phase 3: build the transit rows of the multi-sector supply inventory.

Two agencies:
  kcmetro        King County Metro   (a King County department)
  sound_transit  Sound Transit       (a separate regional authority)

What the evidence says, established in earlier scripts and frozen:

  Metro
    - King County runs an UNRESTRICTED Google Translate widget. No
      includedLanguages parameter, so every language Google supports.
    - Its site-wide "language selector" is populated from that widget's
      option list. It is a machine translation picker, not a menu of
      translated pages.
    - Its seven locale paths (/es-ES etc.) serve English content.
      71 of 77 sampled page/locale pairs are byte-identical to English.
    - Real human translation exists across King County, 247 pages in 34
      languages, but only 2 of those belong to Metro, and one of the two
      is a UI component rather than a content page.
    - Interpreter line 206-553-3000, "nearly 200 languages", advertised
      in English only.

  Sound Transit
    - Also runs an unrestricted Google Translate widget.
    - Publishes an "I Speak" language assistance card in 6 languages.
      This is exactly the artefact rule 4 names as satisfying the
      request-pathway test: a point-to-your-language card.
    - Publishes a 2021 progress report in the same 6 languages.
    - Its Title VI language plan sets a threshold of 25,000+ speakers and
      about 1% of a 1,087 square mile three-county district. No language
      specific to South King County can reach that bar.

The scoring consequence worth understanding before reading the output:

  Rule 4 accepts a machine widget as a DISCOVERY pathway, so an
  unrestricted widget grants oral tier 2 in every language Google
  supports. Both agencies therefore score 2 almost everywhere. That is
  not a finding about generosity, it is the known weakness of tier 2,
  and it is why pathway_type is recorded separately: it separates
  "someone wrote this in your language" from "a machine will guess".

Output: data/inventory/transit_inventory.csv
"""

import json
from datetime import date
from pathlib import Path

import pandas as pd

# ---- tuning constants -------------------------------------------------

SECTOR = "transit"

METRO_ID, METRO_NAME = "kcmetro", "King County Metro"
ST_ID, ST_NAME = "sound_transit", "Sound Transit"

# Both agencies run the default widget with no language restriction.
# Verified in cds.kingcounty.gov/index.js and on soundtransit.org.
METRO_UNRESTRICTED_WIDGET = True
ST_UNRESTRICTED_WIDGET = True

# Metro's own translated content pages, from the frozen King County
# sitemap. The Arabic entry is a shared right-to-left UI component, not a
# page a rider reads, so it is excluded and the exclusion is recorded.
METRO_TRANSLATED = {
    "Tagalog": "/dept/metro/programs-and-projects/future-of-paratransit/tagalog",
}
METRO_EXCLUDED = {
    "Arabic": "shareddata/right-to-left-languages component, a UI fragment, not rider content",
}

# Sound Transit's "I Speak" card, plus the 2021 progress report, both in
# the same six languages.
ST_I_SPEAK = ["Spanish", "Chinese-Mandarin", "Chinese-Cantonese",
              "Vietnamese", "Korean", "Russian", "Tagalog"]
ST_I_SPEAK_URL = ("https://www.soundtransit.org/sites/default/files/documents/"
                  "i-speak-language-assistance-2019.pdf")
ST_I_SPEAK_DATE = "2019-07-05"

METRO_INTERPRETER_URL = ("https://kingcounty.gov/en/legacy/depts/transportation/"
                         "metro/contact-us/need-an-interpreter.aspx")
METRO_WIDGET_URL = "https://kingcounty.gov/en/dept/metro"
ST_TITLE_VI_URL = ("https://www.soundtransit.org/get-to-know-us/"
                   "office-civil-rights-equity-inclusion/title-vi-civil-rights/"
                   "registering-complaint")

# Canonical study-area names that Google labels differently. Each is a
# naming difference, not a coverage gap; checking only exact names
# reported five false absences including Punjabi and Farsi.
GOOGLE_ALIASES = {
    "Farsi": "Persian",
    "Tagalog": "Filipino",
    "Burmese": "Myanmar (Burmese)",
    "Punjabi": "Punjabi (Gurmukhi)",
    "Portuguese": "Portuguese (Brazil)",
    "Chinese-Mandarin": "Chinese (Simplified)",
    "Chinese-Cantonese": "Chinese (Traditional)",
    "American Sign Language": None,   # not a written language, no widget path
}

OUT = Path("data/inventory/transit_inventory.csv")


def google_coverage():
    d = json.loads(Path("data/raw/google_translate_languages.json")
                   .read_text(encoding="utf-8"))["languages"]
    by_name = {v.lower(): k for k, v in d.items()}

    def covered(lang):
        if lang in GOOGLE_ALIASES:
            alias = GOOGLE_ALIASES[lang]
            return by_name.get(alias.lower()) if alias else None
        return by_name.get(lang.lower())

    return covered, len(d)


def main():
    today = date.today().isoformat()
    covered, n_google = google_coverage()

    demand = pd.read_csv("data/processed/demand_by_district.csv")
    universe = sorted(set(demand["language"]))
    fam = demand.groupby("language")["families"].sum()

    print(f"Google Translate languages: {n_google}")
    print(f"study-area languages:       {len(universe)}")
    uncovered = [l for l in universe if not covered(l)]
    print(f"NOT covered by the widget:  {len(uncovered)}")
    print(f"  {sorted(uncovered)[:25]}")

    rows = []
    for lang in universe:
        g = covered(lang)

        # ---- Metro ---------------------------------------------------
        m_written = 3 if lang in METRO_TRANSLATED else (1 if g else 0)
        m_oral = 2 if g else 0
        m_notes = []
        if lang in METRO_TRANSLATED:
            m_notes.append("Metro publishes one translated page in this language")
        if lang in METRO_EXCLUDED:
            m_notes.append("EXCLUDED from tier 3: " + METRO_EXCLUDED[lang])
        if m_oral == 2:
            m_notes.append("Tier 2 rests entirely on the unrestricted Google "
                           "Translate widget. The interpreter line instruction "
                           "at 206-553-3000 is published in English only")
        else:
            m_notes.append("Not covered by the widget and no in-language "
                           "pathway, so there is no published route to the "
                           "interpreter line in this language")
        rows.append({
            "agency_id": METRO_ID, "agency_name": METRO_NAME, "sector": SECTOR,
            "language": lang,
            "written_tier": m_written, "oral_tier": m_oral, "collection_tier": "",
            "pathway_in_language": bool(g),
            "pathway_type": "machine_widget" if g else "none",
            "translated_page_count": 1 if lang in METRO_TRANSLATED else 0,
            "translated_page_slugs": METRO_TRANSLATED.get(lang, ""),
            "evidence_url": (("https://kingcounty.gov/en" + METRO_TRANSLATED[lang])
                             if lang in METRO_TRANSLATED else METRO_INTERPRETER_URL),
            "capture_date": today,
            "notes": " | ".join(m_notes),
            "assigned_by": "EH", "assignment_method": "derived",
        })

        # ---- Sound Transit -------------------------------------------
        in_card = lang in ST_I_SPEAK
        s_written = 3 if in_card else (1 if g else 0)
        s_oral = 2 if (in_card or g) else 0
        s_notes = []
        if in_card:
            s_notes.append(f"On the 'I Speak' language assistance card, last "
                           f"updated {ST_I_SPEAK_DATE}. Rule 4 accepts a "
                           f"point-to-your-language card as a pathway")
            s_notes.append("Also has a 2021 system expansion progress report "
                           "in this language")
        elif g:
            s_notes.append("Tier 2 rests entirely on the unrestricted Google "
                           "Translate widget")
        else:
            s_notes.append("No widget coverage and not on the I Speak card")
        s_notes.append("Sound Transit's Title VI threshold is 25,000+ speakers "
                       "and about 1% of a 1,087 sq mi three-county district. No "
                       "language specific to South King County can reach it")
        rows.append({
            "agency_id": ST_ID, "agency_name": ST_NAME, "sector": SECTOR,
            "language": lang,
            "written_tier": s_written, "oral_tier": s_oral, "collection_tier": "",
            "pathway_in_language": bool(in_card or g),
            "pathway_type": ("in_language_document" if in_card
                             else "machine_widget" if g else "none"),
            "translated_page_count": 2 if in_card else 0,
            "translated_page_slugs": "i-speak-card; 2021-progress-report" if in_card else "",
            "evidence_url": ST_I_SPEAK_URL if in_card else ST_TITLE_VI_URL,
            "capture_date": today,
            "notes": " | ".join(s_notes),
            "assigned_by": "EH", "assignment_method": "derived",
        })

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"\nwrote {OUT}  ({len(df)} rows)")

    df["families"] = df["language"].map(fam).fillna(0).astype(int)
    print("\npathway_type by agency, weighted by families:")
    piv = df.pivot_table(index="pathway_type", columns="agency_name",
                         values="families", aggfunc="sum", fill_value=0)
    print(piv.to_string())

    print("\nlanguages where an agency reaches tier 3 (a real document):")
    t3 = df[df["written_tier"] == 3].sort_values("families", ascending=False)
    print(t3[["agency_name", "language", "families"]].to_string(index=False))


if __name__ == "__main__":
    main()
