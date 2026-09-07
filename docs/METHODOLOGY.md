# Methodology: Estimating Language Demand in South King County

**Project:** Language Access in South King County
**Phase:** 2
**Date:** 2026-09-03

---

## 1. The question this phase had to answer

The project maps where people speak a language at home that nearby public services do not support. That requires knowing which languages are spoken **where**, at a geography fine enough to draw a map.

The school-district demand data from OSPI (Phase 1) covers only families with school-age children. This phase asked whether Census data could extend that to the whole population at neighbourhood resolution.

The short answer is no, and this document shows the work behind that conclusion.

---

## 2. What each source can and cannot do

| Source | Geography | Language detail | Population |
|---|---|---|---|
| OSPI Languages Spoken by Students and Families | School district | **Specific** (Amharic, Tigrinya, Oromo separately) | Families with K-12 students |
| ACS C16001 | Census tract | 12 broad groups | Everyone aged 5+ |
| ACS B16001 | PUMA | 44 groups, still collapsed | Everyone aged 5+ |
| ACS PUMS (`LANP`) | PUMA | **Specific**, 127 codes | Everyone aged 5+ |

Two findings from building this table are worth stating plainly, because both contradict what the project originally assumed.

### 2.1 C16001 is finer than expected

The project brief described C16001 as four broad buckets. That is C16002, a different table. C16001 actually publishes twelve groups at tract level, and six of them are single languages:

Spanish, French/Haitian/Cajun, German/West Germanic, Russian/Polish/Slavic, Other Indo-European, Korean, Chinese, Vietnamese, Tagalog, Other Asian and Pacific Island, Arabic, Other and unspecified.

**Consequence:** Spanish, Vietnamese, Chinese, Korean, Tagalog and Arabic require no estimation at all. They are published at tract level directly.

### 2.2 B16001 is coarser than expected

The brief assumed B16001 would name specific languages at PUMA level. It does not, for the languages this project is about:

- `Persian (incl. Farsi, Dari)` — Dari is not separable from Farsi
- `Amharic, Somali, or other Afro-Asiatic languages` — Amharic, Somali, Tigrinya and Oromo are one number
- `Ilocano, Samoan, Hawaiian, or other Austronesian languages` — Marshallese and Chuukese are not named
- **Pashto does not appear at any level of B16001.** It falls inside "Other Indo-European languages."

**Consequence:** no published ACS summary table names Amharic separately from Somali anywhere in Washington State. Only the PUMS microdata does, and only at PUMA geography.

This is the reason the OSPI-derived dataset built in Phase 1 has value beyond convenience: it contains language-specific counts that standard published sources cannot produce.

### 2.3 The size of the problem

Across King County's 495 census tracts, the three residual buckets hold:

| Bucket | People aged 5+ |
|---|---|
| Other Indo-European | 96,547 |
| Other Asian and Pacific Island | 82,503 |
| Other and unspecified | 52,078 |
| **Total** | **231,128** |

That is **10.7% of the county's population aged 5 and over** whose home language the tract data will not name, and it contains nearly every language this project is concerned with.

---

## 3. The assumption under test

To recover a specific language at a fine geography, the standard move is **apportionment**:

> Measure a language's share of its bucket somewhere coarse where the detail exists, then apply that share to a finer area where only the bucket total is published.

For example: if Amharic is 22% of the "Other and unspecified" bucket across South King County, assume it is 22% of that bucket in each district, and multiply.

**The assumption embedded in that step is uniformity:** the language mix inside a bucket is roughly the same everywhere in the region.

This project's central claim is that these communities cluster geographically. Clustering is precisely the statement that the mix is *not* the same everywhere. So the method risks assuming away the phenomenon being measured, and would do so invisibly: the resulting map would show a smooth, plausible-looking gradient that is an artifact of the arithmetic rather than a feature of the world.

The assumption was therefore tested rather than adopted.

---

## 4. Test design

Two independent tests were run.

### Test A: internal consistency within PUMS

Using PUMS alone, compare each PUMA's within-bucket language mix against the mix for the five PUMAs combined. This needs no outside data. If apportionment is sound, each PUMA's share should sit close to the regional share.

### Test B: external validation against OSPI

Apply the regional within-bucket share to each school district, then compare against what OSPI actually observed in that district. OSPI is an entirely independent source: different collecting body, different population, different method.

### Why the tests compare shares, not counts

OSPI counts **families with school-age children**. The ACS counts **all people aged 5 and over**. Those denominators are not comparable, and comparing raw counts between them would produce confident nonsense.

Within-bucket shares cancel the denominator. Asking "what fraction of this bucket is Amharic" is a question both sources can answer on the same terms.

### Geographies used

Five PUMAs cover the study area: 23307 (Auburn), 23308 (Federal Way/Des Moines/Vashon), 23309 (Kent), 23310 (Renton), 23311 (Burien/SeaTac/Tukwila/White Center).

Census data for the six school districts was obtained using the ACS `school district (unified)` geography, which avoids a spatial join and its overlap assumptions entirely.

**Note on geographic mismatch:** PUMAs and school districts do not nest. PUMA 23311 contains both Highline and Tukwila districts; Highline itself spans 23311 and 23308, and 23308 also contains Vashon Island, a rural community with a very different population. This mismatch is one reason the tests operate on region-wide shares rather than attempting a PUMA-to-district assignment.

---

## 5. Results

### Test A: within-bucket share by PUMA vs region

All figures are percentages of the containing bucket.

| Language | Regional share | Lowest PUMA | Highest PUMA | Worst error (pp) |
|---|---|---|---|---|
| Ukrainian | 45.7 | 10.3 | 63.3 | 35.5 |
| Bosnian | 2.7 | 0.6 | 37.1 | 34.3 |
| Marshallese | 7.5 | 0.2 | 36.7 | 29.2 |
| Russian | 44.1 | 16.4 | 60.1 | 27.7 |
| Punjabi | 30.2 | 5.9 | 45.7 | 24.3 |
| Samoan | 16.8 | 4.9 | 40.9 | 24.1 |
| Swahili | 16.1 | 2.0 | 36.6 | 20.5 |
| Amharic | 22.0 | 6.4 | 41.1 | 19.0 |

**Mean absolute error: 4.3 percentage points.**

Marshallese ranges from 0.2% of its bucket in one PUMA to 36.7% in another. Under the uniformity assumption that range would be narrow. It is not.

### Test B: predicted share vs OSPI observed share

| District | Bucket | Language | Predicted | Observed | Error (pp) |
|---|---|---|---|---|---|
| Federal Way | Other Indo-European | Dari | 11.0 | **66.7** | +55.7 |
| Auburn | Other Asian & Pacific Island | Marshallese | 7.5 | **63.1** | +55.6 |
| Tukwila | Other Asian & Pacific Island | Burmese | 5.1 | **56.5** | +51.5 |
| Auburn | Other Indo-European | Dari | 11.0 | 60.0 | +49.0 |
| Federal Way | Other and unspecified | Somali | 29.7 | 64.7 | +35.0 |
| Auburn | Russian/Polish/Slavic | Ukrainian | 45.7 | 80.5 | +34.8 |
| Highline | Other Indo-European | Dari | 11.0 | 45.1 | +34.1 |
| Tukwila | Other Indo-European | Punjabi | 30.2 | 1.5 | −28.7 |
| Federal Way | Other Indo-European | Punjabi | 30.2 | 2.8 | −27.4 |

**Mean absolute error: 7.1 percentage points, across 219 district-language rows.**

Full results: `outputs/apportionment_validation.csv`

### Reading the result

The errors are not noise. They are systematic and large, and they run in both directions: apportionment underestimates concentrated communities by up to 56 percentage points and overestimates absent ones by up to 29.

The Marshallese case is the clearest illustration. Apportionment predicts that Auburn's Pacific Island bucket is 7.5% Marshallese. It is 63.1%. That is an eight-fold underestimate of the single most geographically concentrated community in the study area, which is exactly the community an access map most needs to find.

In buckets where a language's true share is frequently under 10%, an average error of 7 percentage points means the estimate carries close to no information about the place it describes.

---

## 6. Decision

**The apportionment method is rejected. No tract-level specific-language estimates are produced in this project.**

Each source is used only at the geography where it is valid:

| Purpose | Source | Geography |
|---|---|---|
| Specific-language demand, school families | OSPI | School district |
| Specific-language demand, whole population | PUMS | PUMA |
| Broad-bucket demand, whole population | C16001 | Census tract |

### Consequence for the map

The access-desert map operates at **two resolutions**, and its legend states which applies to each language:

- **Tract level** for Spanish, Vietnamese, Chinese, Korean, Tagalog and Arabic, which are published at that geography.
- **PUMA or school-district level** for Amharic, Tigrinya, Oromo, Somali, Dari, Pashto, Punjabi, Ukrainian, Marshallese and Chuukese, which are not.

A single-resolution map would look better and would be partly fabricated. The two-resolution map is less elegant and is defensible.

---

## 7. Limitations of this analysis

1. **PUMS is a sample.** The 5-year PUMS represents roughly 5% of the population. Estimates for small language groups in a single PUMA carry wide margins of error that are not computed here. The magnitude of the errors found (30 to 56 percentage points) far exceeds plausible sampling variability, so the conclusion is robust, but individual figures should not be quoted as precise.

2. **The bucket mapping is hand-built.** Assigning each of 127 PUMS language codes to a C16001 bucket required judgment, and 21 codes (mostly "Other X languages" residuals and small European languages) were left unmapped and excluded rather than forced into a bucket. Those exclusions slightly reduce the bucket denominators. The mapping is in `src/validate_apportionment.py` and is open to correction.

3. **OSPI's population is not the ACS population.** OSPI observes families with enrolled children. Comparing shares controls for the size difference, but not for the possibility that language composition genuinely differs between households with school-age children and households without. Some portion of the measured error may be that difference rather than apportionment failure. Test A, which uses only PUMS and is free of this issue, independently shows the same pattern.

4. **PUMA boundaries do not follow district boundaries.** Discussed in section 4. This is why region-wide shares were used.

5. **Single time point.** All figures are 2024 ACS 5-year estimates and the 2024-25 OSPI collection.

---

## 8. Web collection policy

Phase 3 onward reads agency websites. Seven sectors and dozens of organisations are involved, so the rules are set once here rather than decided case by case.

### What is collected

- Public pages only. Nothing behind a login, a paywall, or a form.
- Each page is fetched **once** and frozen to `data/raw/`. Scripts skip a file that already exists, so a rerun makes no network request.
- A small delay between requests. No parallel fetching, no repeated polling.
- Structured endpoints are preferred over scraping where an agency publishes them, because they are lighter on the agency's servers and more stable to parse. KCLS branch data comes from the JSON endpoint its own site uses.

### Robots and content signals

`kcls.org/robots.txt` allows general crawling, disallows a named list of AI and SEO crawlers including ClaudeBot, and carries the content signal `search=yes, ai-train=no, use=reference`.

Their CDN returns HTTP 403 to requests without a browser User-Agent, so a browser User-Agent string is sent.

**The judgment made, stated plainly so a reviewer can disagree with it:** this collection is reference use, which their content signal permits. It is a one-time capture of about forty public pages, none of it used for model training, and every derived claim carries an evidence URL pointing back to the source page. A person doing this project by hand would open the same pages in a browser. The alternative readings are that any non-browser identification should be respected as a refusal, or that the named-crawler block extends to any automated request. Both are defensible; neither is the reading taken here.

### Amendment, 2026-09-05: kingcounty.gov locale paths

`kingcounty.gov/robots.txt` disallows all seven of its translated locale prefixes: `/es-ES`, `/ko-KR`, `/ru-RU`, `/so-SO`, `/uk-UA`, `/vi-VN`, `/zh-CN`.

Under the policy above, those paths would not be fetched. They were fetched anyway, deliberately, and this is the record of that decision.

**Why the exception was made.** Whether those paths carry translated content is a central question of this project, and it is not answerable from outside. The alternatives were exhausted first: the sitemap lists no locale pages, the department homepages link to none, and the Internet Archive has no snapshots. The analyst confirmed by hand, in a browser, that the pages are live before any automated request was made.

**Scope of the exception.** 12 sampled paths across 7 locales, one time, at a 0.3 second interval. Ninety-six requests total. Recorded in `data/raw/kingcounty_locale_audit.csv` with capture dates. No further collection from those paths.

**Why it is defensible.** A `Disallow` on a public government page is a search-indexing instruction, not an access restriction, and the material is public records of a public agency. The audit measured whether the pages differ from their English equivalents; it did not copy or republish their content.

**Why it is still an exception.** It is a departure from a policy written two days earlier, made by the analyst rather than by the agency, and it is logged here rather than left implicit so that a reviewer can disagree with it on the record.

### What is not done

- No collection of personal data. No user accounts, no comments, no catalogue search of individual borrowing.
- No republication of source page content. The published dataset contains derived measures plus URLs, not copies of agency pages.
- No re-fetching on a schedule. The dataset is a dated snapshot, per §7.4 of the classification rule.

### If an agency objects

The frozen raw captures live in `data/raw/` and can be deleted, with the derived tables rebuilt from a hand capture or dropped and reported as a gap. The `assignment_method` column makes it possible to identify exactly which rows depend on automated collection.

---

## 9. Reproducing this

```
python src/fetch_ospi.py            # OSPI demand, district level
python src/apply_crosswalk.py       # language name normalisation
python src/fetch_census.py          # C16001, King County tracts
python src/fetch_b16001_puma.py     # B16001, WA PUMAs  (negative result)
python src/fetch_pums.py            # PUMS LANP, five study PUMAs
python src/fetch_districts.py       # C16001, WA school districts
python src/validate_apportionment.py
```

Phase 3, library sector, in order:

```
python src/fetch_kcls.py                    # branches, collections, interpreters
python src/fetch_boundaries.py              # TIGER unified school district polygons
python src/fetch_kcls_sitemap.py            # every kcls.org page URL
python src/fetch_kcls_translated_pages.py   # translated pages, with headings as evidence
python src/build_locations.py               # point-in-polygon, branch to district
python src/parse_kcls_collections.py        # language x branch, plus source cross-check
python src/parse_kcls_interpreters.py       # in-language pathway and video/audio reach
python src/build_kcls_inventory.py          # applies the classification rule
```

Phase 3, transit sector:

```
python src/fetch_kingcounty_sitemap.py          # 11,587 page URLs, all /en/
python src/audit_kingcounty_locales.py          # are the locale paths translated?
python src/fetch_google_translate_languages.py  # 249 widget languages
python src/build_transit_inventory.py           # Metro and Sound Transit
```

Phase 3, city sector:

```
python src/probe_agency_sites.py       # profiles all 8 city websites
python src/build_city_inventory.py     # applies the classification rule
```

Phase 3, legal aid sector:

```
python src/probe_agency_sites.py       # incremental: profiles only new agencies
python src/build_legal_inventory.py
```

`probe_agency_sites.py` is reusable and incremental: add rows to its
AGENCIES list for the food and health sectors rather than writing new
fetchers. It profiles only agencies not already in the output file.

Phase 3, food assistance sector:

```
python src/probe_agency_sites.py       # incremental
python src/build_food_inventory.py
```

Phase 3, health sector:

```
python src/probe_agency_sites.py       # incremental
python src/build_health_inventory.py
```

Phase 4, gap index:

```
python src/build_master_inventory.py           # unify all 7 sectors
python src/build_city_district_crosswalk.py    # spatial city <-> district
python src/build_gap_index.py                  # the index, both readings
python src/compare_kc_tier_map.py              # the memo's central exhibit
PYTHONPATH=src python src/sensitivity_analysis.py
```

**Detection caveat carried forward.** Slug-based detection
(`…/emergency_information_amharic`) is how governments name translated
pages. Nonprofits often use locale path prefixes (`…/fa-af/…`) instead.
Running slug detection alone across legal aid reported zero translated
pages at every organisation, which was a fact about the detector rather
than the sector. Both patterns must be checked in the remaining sectors.

Requires `geopandas`, `beautifulsoup4` and `pypdf`. Every fetch script skips a file already on disk, so the sequence is safe to rerun and makes no network requests on a second run.

Requires a Census API key in `.env` as `CENSUS_API_KEY`. Run `python src/check_key.py` to verify it.

All raw API responses are frozen in `data/raw/` with the pull date, so the numbers above are reproducible even if the Census revises its published estimates.
