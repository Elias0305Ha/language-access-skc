# Data Dictionary

**Project:** Language Access in South King County
**Version:** 1.0
**Last updated:** 2026-09-05

Every table in this repository, what each column means, and what it does not mean.

If you only read one section, read [How to read a tier](#how-to-read-a-tier). Misreading a tier is the single easiest way to draw a wrong conclusion from this dataset.

---

## 1. Directory layout

| Directory | Contents | Edited by hand? |
|---|---|---|
| `data/raw/` | Frozen API responses and source files, exactly as downloaded | **Never** |
| `data/reference/` | Hand-maintained lookups | Yes, deliberately |
| `data/processed/` | Derived tables, rebuilt by scripts | No, regenerate instead |
| `data/inventory/` | The supply inventory, one file per sector | Schools yes, library no |
| `outputs/` | Analysis results | No |
| `docs/` | This file, the classification rule, the methodology |  |
| `src/` | One script, one job |  |

**`data/raw/` is append-only.** Sources revise their published data. A frozen copy is the only way to tell whether a changed number came from your code or from theirs. Fetch scripts skip any file already on disk; to recapture, delete the file by hand.

---

## 2. How to read a tier

A tier is assigned per **(agency, language, mode)**. Never one tier for an agency, never one tier for a language.

### The three modes

| Mode | Column | Question |
|---|---|---|
| Written | `written_tier` | Has this agency communicated with this community in writing, in their language? |
| Oral | `oral_tier` | Can a speaker of this language talk to a human here? |
| Collection | `collection_tier` | Can a speaker of this language borrow material in it? |

The written and oral split exists because a document and an interpreter serve different people. Renton publishes documents in "Chinese" without naming a variety. Written Chinese serves both Cantonese and Mandarin readers. An interpreter does not.

`collection_tier` applies to the library sector only. It is blank elsewhere and that is correct, not missing data.

### The scale

| Tier | Name | Test |
|---|---|---|
| **3** | Human-translated materials | At least one family-facing document exists in this language, human-produced or reviewed |
| **2** | Service on request | A human service can be requested in this language **and the request pathway is reachable by someone who reads only this language** |
| **1** | Machine translation only | Automated page translation exists in this language. Nothing human, no reachable pathway |
| **0** | Nothing | Not offered, not listed, no way to request it |

`collection_tier` uses a reduced scale: **3** = materials for all ages, **2** = children's materials only, **0** = none. **1 is never used**, because there is no machine-translated book.

### The two rules that trip people up

**Tier 2 requires the pathway itself to be in that language.** An English-only page saying "interpreters available in any language" is **tier 0**, not tier 2. A service a family cannot discover is not a service. This is the most consequential decision in the project and the full reasoning is in `CLASSIFICATION_RULE.md` §4.

**Tiers are a ceiling, not a sum.** An agency with human-translated documents is tier 3 even if it also runs a translation widget. Record the highest level reached, and put depth in its own column.

---

## 3. Conventions that apply to every table

| Convention | Why |
|---|---|
| `language` is always a canonical name from `language_crosswalk.csv` | OSPI, Census and agencies all spell languages differently |
| `evidence_url` points at the **specific page** the tier came from, never a homepage | A tier without evidence is an opinion |
| `capture_date` is mandatory | Websites change. Without it the dataset cannot be defended in six months |
| Free-text columns (`notes`, `reason`) are prose and contain commas | Always read with a real CSV parser, never split on commas |
| Excluded rows are counted and reported, never dropped silently | A total that does not reconcile is worse than a smaller total that does |
| Raw files are read as strings first | Suppressed cells contain words, not numbers. Reading as numbers turns them into blanks and you never learn what you lost |

---

## 4. Demand tables

### `data/processed/demand_by_district.csv` — 443 rows

Who speaks what, by school district. Built from OSPI 2024-25 by `build_demand.py` then `apply_crosswalk.py`.

| Column | Type | Meaning |
|---|---|---|
| `DistrictName` | text | One of the six study districts, full official name |
| `language` | text | Canonical language name |
| `families` | integer | Families reporting this as their preferred language of communication |

**`families` is families, not people and not students.** It covers only households with a K-12 student enrolled in that district. It says nothing about adults without school-age children, which is the single biggest limitation of this dataset and the reason Phase 2 exists.

### `data/processed/languages_all.csv` — 213 rows

Every language OSPI reports statewide, before filtering to the study area. Kept so the study-area filter can be checked rather than trusted.

| Column | Type | Meaning |
|---|---|---|
| `LanguageName` | text | OSPI's own spelling, **not** canonical |
| `preferred_families` | integer | Statewide family count |

### `data/processed/pums_language_by_puma.csv` — 382 rows

Census PUMS person records aggregated to PUMA and specific language.

| Column | Type | Meaning |
|---|---|---|
| `puma` | text | 5-digit PUMA code. The five study PUMAs are 23307, 23308, 23309, 23310, 23311 |
| `language` | text | Specific language from the PUMS `LANP` variable, 127 codes |
| `people` | integer | **Sum of `PWGTP`**, the sampling weight, not a row count |
| `puma_name` | text | Human-readable PUMA description |

**Never count PUMS rows.** Each record carries a sampling weight and represents many people. Counting rows produces plausible-looking numbers wrong by roughly a factor of twenty.

**PUMAs and districts do not nest.** PUMA 23311 contains both Highline and Tukwila. Highline spans 23311 and 23308. 23308 also contains Vashon Island, which resembles nothing else in it.

---

## 5. Reference tables (hand-maintained)

### `data/reference/language_crosswalk.csv` — 40 rows

Normalises language names to canonical form.

| Column | Type | Meaning |
|---|---|---|
| `source_name` | text | The spelling as it appears in a source |
| `canonical_name` | text | The name used everywhere in this project |
| `decision` | text | `keep` if already canonical, `merge` if folded into another name |
| `reason` | text | Why, in prose |

**Ambiguous labels are left unresolved and counted, not guessed.** "Ethiopic" is a writing system, not a language, so it is not folded into Amharic. About 1.0% of OSPI records remain unresolved and are reported as such rather than assigned.

### `data/reference/kcls_language_map.csv` — 29 rows

Maps KCLS's own language labels to canonical names. Separate from the crosswalk because it is **one-to-many and mode-dependent**.

| Column | Type | Meaning |
|---|---|---|
| `kcls_label` | text | The label exactly as KCLS writes it, native script included |
| `canonical_name` | text | Canonical language this label serves |
| `applies_to_modes` | text | Comma-separated subset of `written`, `oral`, `collection` |
| `reason` | text | Why this mapping, in prose |

The mode scope is the load-bearing part. Two examples:

- **`中文 – Chinese` produces two rows.** Chinese-Mandarin gets `written, oral, collection`. Chinese-Cantonese gets `written, collection` only, because KCLS names Mandarin as its available interpreter and an interpreter is variety-specific.
- **`فارسی – Persian` produces two rows.** Farsi and Dari both get `collection`, because they share a written standard, so Persian-language material is readable by Dari readers.

Get the mode scope wrong and you credit an agency with a service it does not provide.

---

## 6. Supply inventory

One file per sector. **`sector` values:** `schools`, `library`, `transit`, `city`, `legal`, `food`, `health`.

### `data/inventory/school_inventory.csv` — 60 rows

Six districts by their top ten languages. **Hand-scored by one person.**

| Column | Type | Meaning |
|---|---|---|
| `agency_name` | text | Full official district name |
| `sector` | text | `schools` |
| `language` | text | Canonical language name |
| `families` | integer | From the demand table. Present because a district is both agency and geography |
| `written_tier` | 0-3 | See §2 |
| `oral_tier` | 0-3 | See §2. Tier 3 here means a **named in-house bilingual staff member**, not a phone contract |
| `evidence_url` | url | The specific page scored |
| `capture_date` | date | ISO 8601 |
| `translated_doc_count` | integer | Tier 3 only. Depth, kept out of the tier |
| `translated_doc_types` | text | e.g. enrollment, discipline, special education |
| `pathway_in_language` | boolean | Whether §4 was satisfied |
| `notes` | text | Contradictions and anything a reviewer should see |
| `assigned_by` | text | Analyst initials |

### `data/inventory/library_inventory.csv` — 140 rows

King County Library System against every language in demand. **Derived by code**, not hand-scored.

| Column | Type | Meaning |
|---|---|---|
| `agency_id` | text | `kcls`. Stable key, unlike a display name |
| `agency_name` | text | King County Library System |
| `sector` | text | `library` |
| `language` | text | Canonical language name |
| `written_tier` | 0-3 | 3 if any translated page exists. **Never 1**, because KCLS runs no translation widget, so tier 1 is unreachable |
| `oral_tier` | 0-2 | 2 if an in-language request page exists. **Capped at 2**: KCLS publishes no bilingual staff roster, so tier 3 cannot be evidenced |
| `collection_tier` | 0, 2, 3 | See §2 |
| `pathway_in_language` | boolean | Whether §4 was satisfied |
| `translated_page_count` | integer | Distinct translated pages found in the sitemap |
| `translated_page_slugs` | text | Semicolon-separated, so any count can be audited |
| `oral_locations_phone` | integer | Study-area locations with phone interpreting. 22 |
| `oral_locations_video` | integer | Study-area locations with video or audio interpreting. 20 |
| `oral_availability` | text | `always` or `weekdays`. Only five languages are available outside weekday hours |
| `collection_branches` | integer | Study-area branches holding material in this language |
| `collection_branch_names` | text | Semicolon-separated |
| `evidence_url` | url | Specific page |
| `capture_date` | date | ISO 8601 |
| `notes` | text | Prose |
| `assigned_by` | text | `EH` |
| `assignment_method` | text | `derived` or `manual`. See below |

**No `families` column, deliberately.** KCLS is one agency spanning six districts and 22 locations. There is no families count that belongs on a KCLS row. Demand meets supply in Phase 4, by geography, once.

### `assignment_method`

| Value | Meaning |
|---|---|
| `manual` | A person read the page and assigned the tier |
| `derived` | Code applied the classification rule to frozen structured evidence |

A `derived` row is exactly reproducible and removes the single-coder problem for that sector. It is **not automatically more accurate**: it faithfully propagates the agency's own errors, including the three places KCLS contradicts itself.

### Known schema divergence

`school_inventory.csv` predates the multi-sector schema and differs from it:

| Column | Schools | Library |
|---|---|---|
| `agency_id` | absent | present |
| `families` | present | absent by design |
| `assignment_method` | absent (all rows are `manual`) | present |
| `collection_tier` | absent (not applicable) | present |
| translated-doc depth | `translated_doc_count`, `translated_doc_types` | `translated_page_count`, `translated_page_slugs` |

**The library schema is the standard for the five remaining sectors.** Bringing schools onto it is an additive change and is listed in §10.

---

## 7. Library sector working tables

### `data/processed/kcls_locations.csv` — 51 rows

Every KCLS location, geocoded, assigned to a school district.

| Column | Type | Meaning |
|---|---|---|
| `agency_id` | text | `kcls` |
| `location_id` | text | `kcls-<KCLS id>` |
| `location_name` | text | Cleaned name, e.g. `Kent` |
| `location_name_raw` | text | As published, e.g. `Kent Closed. Holds Pickup at Kent Panther Lake.` Never overwritten |
| `location_type` | text | `branch`, `closed`, `locker`, `admin`, `express` |
| `street`, `city`, `state`, `zip` | text | Postal address as published |
| `lat`, `lon` | float | WGS84, **EPSG:4326**, supplied by KCLS |
| `web_url` | url | The branch page |
| `district_geoid` | text | Census GEOID of the containing district, blank if outside all six |
| `district_name` | text | e.g. `Highline School District` |
| `in_study_area` | boolean | True if inside one of the six districts. **22 are** |

**`district_name` comes from point-in-polygon, never from `city`.** Filtering on `city` is wrong and wrong in the places that matter most:

| Branch | `city` says | Actually in |
|---|---|---|
| White Center | Seattle | Highline |
| Boulevard Park | Seattle | Highline |
| Greenbridge | Seattle | Highline |
| Skyway | Seattle | **Renton** |
| Woodmont | Des Moines | **Federal Way** |

Skyway is one of only two branches in the county holding Amharic material. A city-name filter halves the Amharic result with no error and no warning.

**`location_type` is not `branch` for four rows.** A returns locker cannot lend you an interpreter. They are flagged rather than dropped so the count reconciles.

### `data/processed/kcls_collections.csv` — 272 rows

One row per language-location pair with borrowable material.

| Column | Type | Meaning |
|---|---|---|
| `agency_id` | text | `kcls` |
| `language_native` | text | e.g. `አማርኛ` |
| `language_english` | text | KCLS's English label, **not canonical**. Map via `kcls_language_map.csv` |
| `location_slug` | text | Slug from the source URL |
| `location_name` | text | Joined to the locations table. Blank if unrecognised |
| `is_physical` | boolean | False for `Outreach`, a mobile service with no address |
| `children_only` | boolean | True where KCLS states children's materials only |
| `evidence_url` | url | The exact link parsed |
| `source_view` | text | `by_language` |

### `data/processed/kcls_interpreter_languages.csv` — 9 rows

The languages in which KCLS publishes its interpreter request page. This table **is** the §4 pathway evidence for the library sector.

| Column | Type | Meaning |
|---|---|---|
| `agency_id` | text | `kcls` |
| `language_english` | text | Mapped from the URL slug |
| `language_native` | text | The link text a reader actually sees |
| `pathway_in_language` | boolean | Always true in this table |
| `evidence_url` | url | The translated page, all nine verified HTTP 200 |
| `slug` | text | KCLS's own slug |

**One source error preserved here.** KCLS labels one link **پښتو**, which is Pashto, but uses the slug `pa`, which is the ISO 639-1 code for Punjabi. Pashto is `ps`. The page heading is **ژباړونکي**, Pashto script. The label is followed, not the slug, and the anomaly is recorded rather than corrected.

### `data/processed/kcls_interpreter_locations.csv` — 36 rows

Branches offering video or audio interpreting, funded by a Washington State Library grant. Phone interpreting is available at **every** branch and is therefore not in this table.

| Column | Type | Meaning |
|---|---|---|
| `location_name` | text | As printed on the interpreters page |
| `agency_id` | text | `kcls` |
| `video_audio_interpreting` | boolean | Always true in this table |
| `district_name` | text | Joined from the locations table |
| `in_study_area` | boolean | **20 of 36 are** |
| `location_type` | text | Joined from the locations table |

Study-area locations **without** video or audio: `Muckleshoot` and `Normandy Park Lockers`.

### `data/raw/kcls_translated_pages.csv` — 29 rows

Every translated page found in the kcls.org sitemap, with its heading as evidence.

| Column | Type | Meaning |
|---|---|---|
| `language` | text | Inferred from the URL suffix |
| `slug` | text | e.g. `library-cards-es` |
| `url` | url | Full URL |
| `http_status` | integer | Verified live at capture |
| `h1` | text | The page's own heading, recorded verbatim |
| `h1_non_latin` | boolean | True if the heading is in non-Latin script |
| `capture_date` | date | ISO 8601 |

**Why the heading is stored rather than a verdict.** A URL suffix is not proof of a translation. `library-cards-es` is headed *"Obtenga una tarjeta de biblioteca"*, a genuine Spanish page. `best-books-es` is headed *"Best Books (Spanish)"*, an English page listing Spanish books. Counting suffixed URLs alone scores those identically. Of 20 Spanish-suffixed pages, roughly 10 carry a Spanish heading. `h1_non_latin` can only prove a non-Latin heading, so Spanish and Somali still need reading by eye.

---

## 8. Outputs

### `outputs/gap_index_phase1.csv` — 60 rows

Demand joined to school supply, reporting the shortfall three ways. Weights are constants at the top of `build_gap_table.py` so Phase 4 can sweep them.

| Column | Type | Meaning |
|---|---|---|
| `agency_name`, `sector`, `language`, `families` | | From the inventory |
| `written_tier`, `oral_tier` | 0-3 | From the inventory |
| `written_gap` | float | `families x SHORTFALL_WRITTEN[written_tier]` |
| `oral_gap` | float | `families x SHORTFALL_ORAL[oral_tier]` |
| `gap_score` | float | `0.7 x written_gap + 0.3 x oral_gap`. Volume-sensitive, answers "how many people" |
| `severity` | float 0-1 | `gap_score / families`. Population-independent, answers "how badly served" |
| `families_unserved` | integer | `families` where `written_tier == 0`, else 0. No weights, nothing to argue with |
| `evidence_url`, `capture_date`, `notes` | | From the inventory |

**Shortfall weights.** Fraction of need still unmet at each tier:

| Tier | Written | Oral |
|---|---|---|
| 3 | 0.00 | 0.00 |
| 2 | 0.60 | 0.20 |
| 1 | 0.85 | 0.70 |
| 0 | 1.00 | 1.00 |

The **2-to-3 step is deliberately the largest on the written side**. An unrestricted Google Translate widget covers 135+ languages, so tier 2 is nearly free for any agency running the default and does not discriminate between agencies. Documents that already exist do.

The **oral scale is gentler** because tier 3 oral means a named bilingual staff member, which no district can staff for 193 languages. Charging heavily for its absence made the earlier version of this score track population size instead of unmet need.

**Three numbers, not one.** A single score cannot answer "who is worst" and "who is biggest" at the same time.

### `outputs/apportionment_validation.csv` — 219 rows

The Phase 2 test of whether Census broad-group data can be pushed down to specific languages.

| Column | Type | Meaning |
|---|---|---|
| `DistrictName` | text | Study district |
| `bucket` | text | The ACS broad language group |
| `language` | text | Specific language within that bucket |
| `observed_share` | float 0-1 | This language's actual share of its bucket, from OSPI |
| `regional_share` | float 0-1 | The share apportionment would have predicted |
| `error_pp` | float | Percentage points of error |

**The result is negative and that is the point.** Mean absolute error 7.1 points. Auburn's Marshallese share was predicted at 7.5% and is actually 63.1%. This table is the evidence for the decision not to publish tract-level specific-language estimates.

### `outputs/kcls_source_disagreements.csv` — 6 rows

Places where KCLS's own page contradicts itself. The collections page states its facts twice, once per language and once per location. These are the rows where the two views disagree.

| Column | Type | Meaning |
|---|---|---|
| `location_name` | text | The branch |
| `language` | text | The disputed language |
| `claimed_by` | text | `by_language` or `by_location`, the view asserting it |
| `missing_from` | text | The view that omits it |

**Not resolved, on purpose.** Picking a winner would be inventing data. Three locations are affected: Covington, Renton Highlands, Outreach.

---

## 9. Geography

**Study area:** six school districts. Highline, Tukwila, Kent, Federal Way, Renton, Auburn. Covering SeaTac, Burien, Des Moines, Tukwila, Kent, Federal Way, Renton, Auburn. Charter and tribal schools excluded, noted as a limitation.

**District boundaries:** Census TIGER/Line 2024 Unified School District polygons, `data/raw/tl_2024_53_unsd.zip`, native CRS **EPSG:4269**. This is the polygon form of the same `school district (unified)` geography the ACS pull uses, so a polygon here and an ACS row mean the same thing by construction.

| District | GEOID |
|---|---|
| Auburn | 5300300 |
| Federal Way | 5302820 |
| Highline | 5303540 |
| Kent | 5303960 |
| Renton | 5307230 |
| Tukwila | 5308130 |

**Coordinate reference systems.** Points are **EPSG:4326** (WGS84, what GPS and web APIs emit). Polygons arrive as **EPSG:4269** (NAD83) and are converted explicitly before any join. In this region the two differ by about a metre, which is irrelevant for point-in-polygon, but the same carelessness between a projected CRS in feet and a geographic one in degrees produces answers wrong by thousands of miles. **Always convert. Never let the library assume.**

### What each source can actually resolve

| Source | Geography | Language detail | Population |
|---|---|---|---|
| OSPI | School district | Specific | Families with K-12 students |
| ACS C16001 | Tract, and school district | 12 broad groups | Everyone 5+ |
| ACS B16001 | PUMA | 44 groups, still collapsed | Everyone 5+ |
| ACS PUMS `LANP` | PUMA | Specific, 127 codes | Everyone 5+ |

**No published ACS summary table names Amharic separately from Somali.** B16001 lumps them as "Amharic, Somali, or other Afro-Asiatic languages." Dari is inseparable from Farsi. Pashto and Marshallese are not named at any level. Only PUMS names them.

---

## 10. Open items

- Bring `school_inventory.csv` onto the library schema: add `agency_id` and `assignment_method='manual'`. Additive, no rescoring.
- Blind re-score of a 10-row sample of the school inventory, for an inter-rater reliability figure. Addresses the single-coder weakness.
- Archive evidence URLs at web.archive.org for the rows the memo names.
- Five sectors remaining: transit, city government, legal aid, food assistance, health clinics.

---

## 11. Reproducing everything

Run order is in `METHODOLOGY.md` §9. Every fetch script skips a file already on disk, so the full sequence is safe to rerun and makes no network requests on a second run.

Requires a Census API key in `.env` as `CENSUS_API_KEY`, plus `pandas`, `geopandas` and `beautifulsoup4`.
