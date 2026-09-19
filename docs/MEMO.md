# Language access in South King County: the tier map is the bottleneck

**To:** King County Language Access Program, Office of Equity and Social Justice
`kcla@kingcounty.gov` · 206-477-6608
**From:** Elias Hakenso · Resident, SeaTac · `erdunoelias@gmail.com`
**Date:** 2026-09-07
**Attached:** public dataset, 51 agencies, 6,272 scored rows, every row with an evidence URL

---

## The ask

**Update the County's language tier map.**

That is the whole request. Not a translation budget, not an agency-by-agency audit. One data refresh, already within the Office's authority, maintained jointly with the county demographer.

## Why

King County Code 2.15.030.B requires every County agency to hold a Language Assistance Plan identifying which vital documents must be translated into *"the County's top six languages, based on the County's tier map."*

The tier map in force is Appendix C of policy INF-14-2-AEO. Its own header reads:

> Language-Rank-Tiers-2016Updt-Final.xlsx — **2016 Census Update Data (Most current as of October 2018)**

The Afghan evacuation was August 2021. The full-scale invasion of Ukraine was February 2022.

**Dari is now the second-largest home language in South King County after Spanish, and it does not appear on the tier map at all.**

| Language | Families, six South King County school districts | Tier map status |
|---|---|---|
| Spanish | 19,569 | Tier 1, translation required |
| **Dari** | **3,040** | **absent** |
| Vietnamese | 2,033 | Tier 2, recommended |
| Ukrainian | 1,781 | Tier 2, recommended |
| **Pashto** | **1,127** | **absent** |
| **Marshallese** | **446** | **absent** |

Source: OSPI 2024-25 languages spoken by students and families, Auburn, Federal Way, Highline, Kent, Renton and Tukwila. Counts are households with a K-12 student. The tier map ranks county-wide Limited English Proficiency population, a different measure on a different geography; this table shows scale and recency, not a like-for-like tier calculation.

**Only Spanish sits in Tier 1, the single tier where translation is required.** That is 53.2% of families in the study area. The remaining **17,206 families, 46.8%**, speak a language for which translation is recommended, encouraged, or unmentioned.

## What that produces downstream

Three measurements from County agencies, each with a source:

- **King County publishes seven translated locale paths** (`/es-ES`, `/so-SO`, `/vi-VN`, `/ru-RU`, `/uk-UA`, `/ko-KR`, `/zh-CN`). Sampling 12 pages across all seven, **71 of 77 comparable page pairs carry main-content text identical to their English equivalent.** The six that differ are the homepage, differing only in the page title. The Somali homepage title is "Home".

  Method: 12 English paths were drawn from the County's own sitemap at a fixed stride, so the sample is reproducible without a stored random seed. Each path was fetched under `/en/` and under all seven locale prefixes. Script, style, navigation, header and footer were stripped, the `<main>` block extracted, markup removed and whitespace collapsed; the resulting strings were compared for exact equality. Comparing against the English page rather than running language detection avoids the failure mode where a detector reads a page as translated because of proper nouns. Captured and frozen in `data/raw/kingcounty_locale_audit.csv`. Script: `src/audit_kingcounty_locales.py`.
- **King County's Amharic pages are machine translation**, identified by a native Amharic speaker. Twenty pages across DCHS and DJA.
- **King County Metro publishes two translated pages**, one of which is a right-to-left UI component rather than rider content. Its interpreter line covering "nearly 200 languages" is advertised in English only, and is option 1 on the general call centre number, which is closed weekends and holidays. Buses are not.

For comparison, within the same County: Public Health publishes 99 language-named pages, Judicial Administration 70, Natural Resources 42. **Capacity is not the constraint.** The tier map is what tells each agency whom to write for, and it was drawn before these communities arrived.

## It is achievable, and a Washington agency already does it

**Washington Healthplanfinder** publishes health coverage information in **26 languages**, including Dari, Pashto, Tigrinya, Oromo, Amharic, Somali, Punjabi, Khmer, Lao and American Sign Language. Each carries real in-language text, a translated PDF, and the support line explained in that language.

It does not cover Marshallese either, so it is a model rather than a solved case.

Its Amharic was reviewed by a native speaker for this project and called *"translated perfectly, an example for everyone."*

Same state, same residents, same procurement rules.

## What this looks like on the ground

Across all seven sectors and 51 agencies measured, **393 families have no written provision in their language from any agency at any tier.**

Physical service points tell the same story. **Kent School District has 962 Dari-speaking families and not one library branch or transit service point serving Dari.**

The author lives in SeaTac, whose city website carries 6,719 pages and none in a language other than English, and inside Highline School District, which accounts for six of the eleven district-language pairs scoring maximum severity in this dataset. The Amharic quality checks in this project were made first-hand for that reason.

## Limitations, stated plainly

- Demand comes from OSPI and therefore covers only households with a K-12 student. Adults without school-age children are not counted.
- Provision is measured from what agencies publish online. Services that exist but are not advertised are scored as absent. This understates food banks and clinics in particular.
- **155 tier-3 claims appear in this dataset; two have been read by someone who reads the language.** Two of the four checked Amharic offerings turned out to be machine output. Where the true figure sits inside that range is not known, and the dataset reports both ends rather than one number.
- Informational signage, which KCC 2.15.030.B also requires, cannot be measured by this method and was not attempted.

## One thing the Office already has

Everything above is reproducible. The dataset, the classification rule written before collection began, and the scripts are public. If the tier map is refreshed against current data, the ordinance already in force begins applying to Dari, Pashto and Marshallese without any further action.

**17,206 families move from optional to covered by one administrative update.**
