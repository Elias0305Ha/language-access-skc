"""
Phase 3: build the food assistance rows of the supply inventory.

Selection note. Two kinds of organisation, and they are not comparable on
the same measure, so both are included and the difference is recorded:

  Food banks hand people groceries. A person can collect food with no
  shared language at all, so an English-only website understates them
  more than it understates any other sector in this project. Their rows
  are real but should be read with that in mind.

  The STATE CHANNEL is different. Nobody receives SNAP without submitting
  an application. That form is a consequential document in exactly the
  sense a school placement letter is, and it is the thing worth measuring.

The finding, which DSHS proves against itself.

An earlier version of this analysis said DSHS "does not translate" into
Amharic, Ukrainian, Tigrinya, Punjabi or Arabic. That was wrong, and the
correction makes the finding sharper rather than weaker. DSHS translates
into all of them, and into Marshallese, Karen, Oromo, Lingala and Wolof
besides. It simply does not do it for the application.

Comparing forms from the same agency, same forms library, same year:

    form     non-English  what it is
    -------  -----------  -------------------------------------------
    02-611            32  Statement of Understanding, Mid-Certification
                          Review. A compliance acknowledgement.
    02-528            25  Fair Hearing Withdrawal. The form you sign to
                          GIVE UP your appeal.
    01-205            15  ABAWD work-requirement activity report.
    14-001            12  Application for Cash or Food Assistance.
                          The form that gets you food.

The application has the FEWEST languages of the four.

21 languages get the mid-certification statement and not the
application, covering 17,940 households where DSHS publishes a count.
Among them: Ukrainian 5,881, Arabic 2,447, Punjabi 1,632, Amharic 1,615,
Tigrinya 1,144. Marshallese and Karen get it too, and both are at or near
zero in every other sector of this project.

Stated plainly: DSHS will explain how to withdraw your appeal in Amharic,
Tigrinya, Punjabi, Ukrainian and Arabic. It will not tell you how to
apply for food in any of them.

This is not a capacity finding. The vendors, budget and process plainly
exist. It is a choice about which document is worth translating.

Output: data/inventory/food_inventory.csv
"""

import json
from datetime import date
from pathlib import Path

import pandas as pd

SECTOR = "food"
PROFILES = Path("data/raw/agency_site_profiles.json")
SITEMAPS = Path("data/raw/agency_sitemap_urls.json")
GOOGLE = Path("data/raw/google_translate_languages.json")
QUALITY = Path("data/inventory/quality_checks.csv")
OUT = Path("data/inventory/food_inventory.csv")

FORMS_URL = ("https://www.dshs.wa.gov/office-of-the-secretary/forms"
             "?field_number_value=14-001")

# Form 14-001, Application for Cash or Food Assistance, as listed by DSHS.
# Chinese and Persian each map to two canonical languages, by the same
# written-form rule already applied to Renton's Chinese documents and to
# the library's Persian collection: one written text serves both readers.
DSHS_FORM_LANGUAGES = {
    "Khmer": "Cambodian (Khmer) (Adobe PDF)",
    "Chinese-Mandarin": "Chinese (Adobe PDF)",
    "Chinese-Cantonese": "Chinese (Adobe PDF)",
    "Chuukese": "Chuukese (Trukese) (Adobe PDF)",
    "Korean": "Korean (Adobe PDF)",
    "Lao": "Lao (Adobe PDF)",
    "Pashto": "Pashto (Afghan) (Adobe PDF)",
    "Farsi": "Persian (Farsi / Dari) (Adobe PDF)",
    "Dari": "Persian (Farsi / Dari) (Adobe PDF)",
    "Russian": "Russian (Adobe PDF)",
    "Somali": "Somali (Adobe PDF)",
    "Spanish": "Spanish (Adobe PDF)",
    "Tamil": "Tamil (Adobe PDF)",
    "Vietnamese": "Vietnamese (Adobe PDF)",
}

# DSHS's own monthly count of households by primary language, June 2026.
# Statewide, with no county breakdown, so it cannot serve as a demand
# table for this study area. It is kept because it is an ADMINISTRATIVE
# record naming Dari, Amharic, Tigrigna, Pashto, Chuukese and Oromo
# separately, which no published ACS table does, and because it is the
# evidence for the gap below.
DSHS_CLIENT_LANGUAGES = {
    "Spanish": 105998, "Russian": 12029, "Vietnamese": 9202, "Chinese": 8011,
    "Ukrainian": 5881, "Korean": 3625, "Dari": 2702, "Arabic": 2447,
    "Khmer": 1645, "Punjabi": 1632, "Amharic": 1615, "Portuguese": 1449,
    "Somali": 1417, "Tigrinya": 1144, "French": 994, "Farsi": 990,
    "Tagalog": 871, "Pashto": 680, "Chuukese": 677, "Romanian": 453,
    "Lao": 399, "Burmese": 349, "Swahili": 324, "Haitian Creole": 317,
    "American Sign Language": 298, "Samoan": 261, "Oromo": 252,
    "Thai": 232, "Hindi": 212,
}
DSHS_REPORT_URL = ("https://www.dshs.wa.gov/esa/"
                   "cash-food-and-medical-households-primary-language")

# Other DSHS forms, for the within-agency comparison. The point of this
# table is that translation capacity is not the constraint.
DSHS_OTHER_FORMS = {
    "02-611": ("Statement of Understanding: Mid-Certification Review", 32),
    "02-528": ("Fair Hearing Withdrawal", 25),
    "01-205": ("ABAWD Activity Report", 15),
}
# Languages on 02-611 but not on the application, mapped to canonical names.
IN_MCR_NOT_IN_APPLICATION = [
    "Ukrainian", "Arabic", "Punjabi", "Amharic", "Portuguese", "Tigrinya",
    "French", "Tagalog", "Romanian", "Burmese", "Swahili", "Haitian Creole",
    "Oromo", "Hindi", "Karen", "Marshallese", "Lingala", "Nepali",
    "Bosnian", "Wolof", "Turkish",
]

# Northwest Harvest, from its sitemap: three language-named pages.
NWHARVEST_PAGES = {"Chinese-Mandarin": 1, "Russian": 1, "Vietnamese": 1}

# Applies to every food bank row. Recorded once, in the data, rather than
# left as an unstated caveat in a memo.
FOODBANK_CAVEAT = ("Food bank. Groceries can be collected without a shared "
                   "language, so a web-only assessment understates this "
                   "sector more than any other. Read the tier as a measure "
                   "of published information, not of whether someone is fed")

UNREACHABLE_NOTE = ("Site did not return a usable response under any header "
                    "set tried. Not assessed. Tiers are blank, not zero")

STATE_CHANNEL = {"food_dshs", "food_waconnection"}


def main():
    today = date.today().isoformat()
    profiles = {p["agency_id"]: p for p in
                json.loads(PROFILES.read_text(encoding="utf-8"))}
    google = json.loads(GOOGLE.read_text(encoding="utf-8"))["languages"]
    google_codes = {c.lower() for c in google}
    name_to_code = {v.lower(): k.lower() for k, v in google.items()}

    quality = {}
    if QUALITY.exists():
        for _, r in pd.read_csv(QUALITY).iterrows():
            quality[(r["agency_id"], r["language"])] = r["verdict"]

    demand = pd.read_csv("data/processed/demand_by_district.csv")
    universe = sorted(set(demand["language"]))
    fam = demand.groupby("language")["families"].sum()

    aliases = {"Farsi": "fa", "Dari": "fa", "Tagalog": "tl", "Burmese": "my",
               "Punjabi": "pa", "Chinese-Mandarin": "zh-cn",
               "Chinese-Cantonese": "zh-tw", "Khmer": "km",
               "American Sign Language": None}
    iso_of = {l: (aliases[l] if l in aliases else name_to_code.get(l.lower()))
              for l in universe}

    food_ids = [aid for aid, p in profiles.items() if p.get("sector") == "food"]
    print(f"food assistance agencies: {len(food_ids)}")

    rows = []
    for aid in food_ids:
        p = profiles[aid]
        unreachable = bool(p.get("error")) or p.get("home_status") != 200
        restricted = p.get("widget_restricted_to")
        restricted_set = {c.strip().lower() for c in restricted} if restricted else None
        has_widget = bool(p.get("widgets"))
        is_state = aid in STATE_CHANNEL

        for lang in universe:
            if unreachable:
                rows.append({
                    "agency_id": aid, "agency_name": p["agency_name"],
                    "sector": SECTOR, "language": lang,
                    "written_tier": "", "oral_tier": "", "collection_tier": "",
                    "pathway_in_language": "", "pathway_type": "not_assessed",
                    "translated_page_count": "", "translated_page_slugs": "",
                    "is_state_channel": is_state,
                    "dshs_client_households": DSHS_CLIENT_LANGUAGES.get(lang, ""),
                    "evidence_url": p["base_url"], "capture_date": today,
                    "quality_verdict": "", "notes": UNREACHABLE_NOTE,
                    "assigned_by": "EH", "assignment_method": "unreachable",
                })
                continue

            iso = iso_of.get(lang)
            covered = bool(has_widget and iso and
                           (iso in restricted_set if restricted_set is not None
                            else iso in google_codes))

            docs, slugs, notes = 0, "", []
            if aid == "food_dshs" and lang in DSHS_FORM_LANGUAGES:
                docs, slugs = 1, DSHS_FORM_LANGUAGES[lang]
                notes.append("Form 14-001, Application for Cash or Food "
                             "Assistance, is published in this language")
            if aid == "food_nwharvest" and lang in NWHARVEST_PAGES:
                docs = NWHARVEST_PAGES[lang]
                notes.append(f"{docs} language-named page(s) in the sitemap")

            verdict = quality.get((aid, lang), "unchecked" if docs else "")
            written = 3 if docs else (1 if covered else 0)
            if docs and verdict == "machine":
                written = 1

            ptype = ("in_language_document" if (docs and verdict != "machine")
                     else "machine_widget" if covered else "none")
            oral = 2 if ptype != "none" else 0

            if not has_widget and not docs:
                notes.append("No translation mechanism and no translated "
                             "documents found on the site")
            if not is_state:
                notes.append(FOODBANK_CAVEAT)

            households = DSHS_CLIENT_LANGUAGES.get(lang, "")
            if aid == "food_dshs" and not docs:
                if households:
                    notes.append(f"DSHS's own June 2026 report counts {households:,} "
                                 f"households on cash, food or medical assistance "
                                 f"whose primary language is this one, and it does "
                                 f"not publish the application form in it")
                if lang in IN_MCR_NOT_IN_APPLICATION:
                    notes.append("DSHS DOES publish form 02-611, the "
                                 "Mid-Certification Review statement, in this "
                                 "language, and form 02-528, Fair Hearing "
                                 "Withdrawal, in most of these. Translation "
                                 "capacity is not the constraint; the "
                                 "application is simply not translated")

            rows.append({
                "agency_id": aid, "agency_name": p["agency_name"],
                "sector": SECTOR, "language": lang,
                "written_tier": written, "oral_tier": oral, "collection_tier": "",
                "pathway_in_language": ptype != "none", "pathway_type": ptype,
                "translated_page_count": docs, "translated_page_slugs": slugs,
                "is_state_channel": is_state,
                "dshs_client_households": households,
                "evidence_url": (FORMS_URL if aid == "food_dshs"
                                 else p.get("final_url", p["base_url"])),
                "capture_date": today, "quality_verdict": verdict,
                "notes": " | ".join(notes),
                "assigned_by": "EH", "assignment_method": "derived",
            })

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"wrote {OUT}  ({len(df)} rows)\n")

    t3 = df[df["written_tier"] == 3]
    print("organisations publishing anything in another language:")
    if len(t3):
        for org, sub in t3.groupby("agency_name"):
            langs = sorted(sub["language"])
            print(f"  {org}: {', '.join(langs)}")
    print("\norganisations publishing nothing:")
    none = sorted(set(df[df["assignment_method"] == "derived"]["agency_name"]) -
                  set(t3["agency_name"]))
    for n in none:
        print(f"  {n}")
    print("\nnot assessed:")
    print(f"  {sorted(set(df[df['assignment_method']=='unreachable']['agency_name'])) or 'none'}")

    print("\nWITHIN-AGENCY COMPARISON, DSHS forms library")
    print(f"   {'14-001 Application for Cash or Food Assistance':52}"
          f"{len(set(DSHS_FORM_LANGUAGES.values())):>4} non-English")
    for num, (title, n) in DSHS_OTHER_FORMS.items():
        print(f"   {num + ' ' + title:52}{n:>4} non-English")
    print(f"\n   languages on 02-611 but not on the application: "
          f"{len(IN_MCR_NOT_IN_APPLICATION)}")
    known = {l: DSHS_CLIENT_LANGUAGES[l] for l in IN_MCR_NOT_IN_APPLICATION
             if l in DSHS_CLIENT_LANGUAGES}
    print(f"   households in them where DSHS reports a count: {sum(known.values()):,}")

    # The headline, computed rather than asserted.
    # The client report writes "Chinese"; the form list writes
    # "Chinese-Mandarin"/"Chinese-Cantonese". Comparing the raw keys
    # counted Chinese as having no form and inflated the total by 8,011
    # households. Normalise before differencing.
    form_langs = set(DSHS_FORM_LANGUAGES) | {"Chinese"}
    missing = {l: n for l, n in DSHS_CLIENT_LANGUAGES.items()
               if l not in form_langs}
    print(f"\nDSHS client languages with no application form: {len(missing)}")
    print(f"households in them: {sum(missing.values()):,}")
    for l, n in sorted(missing.items(), key=lambda x: -x[1])[:6]:
        print(f"   {l:24}{n:>8,}")


if __name__ == "__main__":
    main()
