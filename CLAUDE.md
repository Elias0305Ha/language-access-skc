# Language Access in South King County

Project instructions for Claude Code. Read this before doing anything.

---

## How to work with Elias

These are not suggestions. They came from him directly.

- **One step at a time.** Give a single step, wait for him to run it and report back, then give the next. Never dump a sequence of steps.
- **He writes and runs all the code himself.** Do not run scripts for him. Write files into `src/`, show the code in chat so he can read it, and let him execute.
- **Explain the reasoning, not just the instruction.** He is learning to think about this, not just to finish it. Say why a line is written the way it is, especially where a naive version would silently produce wrong output.
- **Be direct and plain. Bullets over paragraphs.**
- **Never use em dashes.** He reads them as AI-written.
- **Never estimate how long something will take him. Never suggest he slow down.** If he is ready for the next step, give the next step.
- **Challenge him.** If he is overcomplicating something, making a bad assumption, or about to ship something indefensible, say so and explain why. He has pushed back and been right before; take his pushback seriously rather than caving to it or defending reflexively.
- **Do not assume background knowledge.** He is experienced with SQL, Python, pandas, SAS, Excel and Git. He is new to GeoPandas, the Census API, DuckDB and Power BI.
- **Check before asserting.** A recurring failure in this project has been stating a fact about a dataset or a website without verifying it, and being wrong. Fetch the metadata, print the columns, look at the page. He has caught several such errors and will catch more.

He speaks Amharic and lives in the study area. On judgment calls about language naming, community boundaries, or what a translated document actually says, his read beats any inference.

---

## What the project is

**The question:** where do people in South King County speak a language at home that the public services around them do not actually serve?

**The method, stripped down:** build a demand table (who speaks what, where), build a supply table (what languages each agency actually provides), join them, subtract, rank, map.

**Study area:** six school districts. Highline, Tukwila, Kent, Federal Way, Renton, Auburn. Covering SeaTac, Burien, Des Moines, Tukwila, Kent, Federal Way, Renton, Auburn.

**Deliverables:** a public dataset, a gap index, an access-desert map, a Power BI dashboard published to Power BI Service, and a one-page memo sent to a real recipient.

**Purpose:** a portfolio project to land data analyst roles and put real Power BI work on his resume. It has to be genuinely good, not a bootcamp exercise.

---

## Where the project stands

### Phase 1: complete

School-sector demand and supply, joined into a gap table.

- OSPI 2024-25 language data pulled and frozen in `data/raw/`
- Language names normalised through a hand-maintained crosswalk, 1.0% left unresolved and counted rather than guessed
- Classification rule written **before** collection began, now at v2.0
- 60-row supply inventory, six districts by top ten languages, every row carrying an evidence URL and capture date
- Gap table reporting three separate measures

**Headline result: 1,428 families have no written provision in their language.** Eleven district-language pairs score a flat 1.00 severity, meaning nothing written and nothing oral. **Highline owns six of them**, Renton three, Federal Way two.

*Corrected 2026-09-07: this note previously read "five" for Highline. Recounted from `outputs/gap_index_phase1.csv`: Highline 6 (Amharic, Pashto, French, Arabic, Tigrinya, Farsi), Renton 3, Federal Way 2.*

### Phase 2: complete

Census integration and the apportionment validation.

**Result: apportionment fails.** Mean absolute error 7.1 percentage points across 219 district-language rows, confirmed independently inside PUMS. Auburn's Marshallese share was predicted at 7.5% and is actually 63.1%.

Written up in `docs/METHODOLOGY.md`.

### Phase 3: complete

Multi-sector supply inventory. **All seven sectors done.** 51 agencies in
`dim_agency.csv`: food 12, health 12, legal 10, city 8, schools 6,
transit 2, library 1.

1. ~~Library (King County Library System)~~ **done, 2026-09-03**
2. ~~Transit (King County Metro, Sound Transit)~~ **done, 2026-09-05**
3. ~~City government (eight cities)~~ **done, 2026-09-05**
4. ~~Legal aid~~ **done**
5. ~~Food assistance~~ **done**
6. ~~Health clinics~~ **done**

The dataset is built. It is not yet on GitHub and there is no README.

**Library sector result.** 51 KCLS locations pulled from their own JSON API with coordinates included, 22 inside the study area, assigned to districts by point-in-polygon against Census TIGER polygons. 140 scored language rows in `data/inventory/library_inventory.csv`.

- **Of the 11 school district pairs scoring a flat 1.00 severity, 10 receive some provision from the library.** Tigrinya in Highline, 54 families, receives nothing from either sector. First true access desert.
- KCLS runs **no translation widget at all**, so tier 1 is unreachable for it. Nine languages have an in-language interpreter request page and score oral tier 2. The rest score 0 despite Language Line covering 240+ languages by phone, because nobody can discover it.
- Amharic: Highline schools publish nothing and offer no pathway. KCLS wrote its interpreter instructions in Amharic. Two public agencies, same neighbourhood, opposite answers. **This contrast is the memo.**

**Tiers in this sector are `assignment_method = derived`**, applied by code to frozen evidence rather than hand-scored. Exactly reproducible. Schools remain `manual`.

**The library schema is the standard for the remaining sectors.** Agency-keyed, no `families` column, demand joins by geography in Phase 4. See `docs/DATA_DICTIONARY.md` §6.

**Transit sector result.** 276 rows, `data/inventory/transit_inventory.csv`.

- Sound Transit publishes an "I Speak" card in 6 languages, covering 23,627 families with a real in-language document. Metro reaches tier 3 in **one** language: Tagalog, 353 families.
- Metro's interpreter line is option 1 on the general call centre number and shares its hours: **closed weekends and holidays**. Buses run on weekends.
- Sound Transit's Title VI threshold is 25,000+ speakers and ~1% of a 1,087 sq mi three-county district. No South King County language can reach it. Same structural point as the Phase 2 result: big geography erases small communities.

**City sector result.** 1,104 rows, `data/inventory/city_inventory.csv`.

- Only three of eight cities publish anything in another language. **Tukwila** (Spanish, Dari, Vietnamese, Somali, Burmese, Nepali), **Burien** (Spanish, Vietnamese, Amharic), **Auburn** (Spanish, Ukrainian).
- Tukwila is the smallest city and the only agency anywhere in the project publishing in Dari, the largest unserved language at 3,040 families.
- **Des Moines** publishes nothing and has no interpreter page: no discoverable pathway in any language.
- **City of Renton curates its widget to 17 languages, including Italian and Indonesian, and omits Dari** — the top severity-1.00 language in Renton School District.

### The quality finding, and why it matters more than any script here

Structural detection can prove a page **exists** in a language. It cannot prove a human wrote it. Elias read the Amharic pages and the two verdicts split:

| Agency | Verdict | Effect |
|---|---|---|
| City of Burien | `human` | tier 3 upheld |
| King County | `machine`, obvious Google Translate | tier 3 → tier 1 |

**This reversed an earlier claim in these notes.** King County's 247 language-named pages across 34 languages were described as human translation and contrasted favourably with Metro. One language was checkable and it was machine output. The other 33 are under suspicion and unverifiable by anyone on this project.

Rule 5.10 now separates `machine` (identification, changes the tier) from `poor` (quality, does not). Verdicts live in `data/inventory/quality_checks.csv`.

**Of 11 tier-3 city rows, exactly 1 has been read by someone who could read it.** Keep that ratio visible; it belongs in the README.

**Bias directions do not cancel.** Limitation 1: English-only web presence understates capacity. Limitation 7: undetected machine translation overstates it. Both are live.

**Elias explicitly rejected cutting this to three sectors and was right to.** The cross-sector comparison is a finding in itself, and the access-desert map needs point density. Do not re-propose narrowing it.

### Phase 4: complete

Master inventory, gap index, access deserts, tier-map comparison.

- `src/build_master_inventory.py` concatenates the per-sector inventories,
  assigns `service_scope` and `tier_verified`.
- `src/build_gap_index.py` scores every district-language pair in two
  readings, optimistic and conservative. Tuning constants at the top.
- `src/build_access_map_layers.py` builds the service-point layers.
- `src/compare_kc_tier_map.py` joins measured demand to King County's
  Appendix C tier map. **The tier map was located**: the PDF is frozen at
  `data/raw/kingcounty_language_tiers_appendixC.pdf`.
- `src/audit_kingcounty_locales.py` tests whether the County's seven
  translated locale paths carry translated content. They mostly do not.

### Phase 5: in progress

- `src/sensitivity_analysis.py` sweeps 11 scenarios. Written up below.
- `src/build_powerbi_model.py` writes the star schema into `powerbi/`.
- `docs/MEMO.md` is written, recipient decided, not yet sent.
- **Power BI report: pages 1 and 2 built. Pages 3 and 4 not started.**
  Spec in `powerbi/BUILD_GUIDE.md` section 5.
- Not done: README, GitHub remote, publish to Power BI Service.

---

## Decisions already made. Do not silently revisit these.

**Study area is six districts.** Charter and tribal schools excluded, noted as a limitation.

**Tiers are assigned per (agency, language) pair, in three modes.** `written_tier`, `oral_tier` and `collection_tier`, each 0 to 3. Never one tier for an agency as a whole. The written/oral split exists because Renton publishes documents in "Chinese" without naming a variety: written Chinese serves both Cantonese and Mandarin readers, interpreters do not. `collection_tier` is library-only and uses a reduced scale; it is blank elsewhere and that is correct, not missing data.

**Tier 2 requires that the request pathway be reachable in that language.** An English-only page saying interpreters are available in any language does not count. This is the most consequential rule in the project. Full reasoning in `docs/CLASSIFICATION_RULE.md` **section 4**. (Section 5 is the decided edge cases. Earlier versions of this file cited section 5 and were wrong.)

**Machine translation counts for discovery, not for documents.** A widget never produces tier 3; it cannot translate PDFs.

**The widget alone does NOT earn tier 2.** This file previously said it did, and that was wrong. `src/build_city_inventory.py` implements the stricter and correct rule:

- `written_tier` 1: no in-language page, but the widget covers the language.
- `oral_tier` 2: the widget covers the language **AND** the city publishes at least one interpreter or language-access page.

The second condition is the point. A widget can only make discoverable something that is already on the page. A city with no interpreter offer anywhere has nothing for the widget to reveal, so it stays below tier 2.

**Consequence to remember:** an unrestricted widget covers 135+ languages, so for any agency that *does* publish an access page, tier 2 is nearly free. Tier 2 discriminates weakly. The gap index therefore weights the 2-to-3 step more heavily than 0-to-2.

**Ambiguous language labels stay unresolved and counted, not guessed.** "Ethiopic" is a writing system, not a language. It is left unassigned rather than folded into Amharic.

**No tract-level specific-language estimates.** Settled by the Phase 2 validation. The map runs at two resolutions and the legend says which.

**Every tier needs an evidence URL and a capture date.** No exceptions.

---

## Data sources and what each can actually do

| Source | Geography | Language detail | Population |
|---|---|---|---|
| OSPI | School district | Specific | Families with K-12 students |
| ACS C16001 | Tract, and school district | 12 broad groups | Everyone 5+ |
| ACS B16001 | PUMA | 44 groups, still collapsed | Everyone 5+ |
| ACS PUMS `LANP` | PUMA | Specific, 127 codes | Everyone 5+ |

Two things worth knowing before touching Census data again:

- **No published ACS summary table names Amharic separately from Somali.** B16001 lumps them as "Amharic, Somali, or other Afro-Asiatic languages." Dari is inseparable from Farsi. Pashto and Marshallese are not named at any level. Only PUMS names them.
- **The ACS publishes `school district (unified)` as a geography.** District-level Census data needs no spatial join. Use it.

**The five study PUMAs:** 23307 Auburn, 23308 Federal Way/Des Moines/Vashon, 23309 Kent, 23310 Renton, 23311 Burien/SeaTac/Tukwila/White Center.

**PUMAs and districts do not nest.** 23311 contains both Highline and Tukwila. Highline spans 23311 and 23308. 23308 also contains Vashon Island, which is nothing like the rest of it.

---

## Repository layout

```
data/raw/          frozen API responses and source files, never edited
data/reference/    hand-maintained lookups (language crosswalk, variable lists)
data/processed/    derived tables
data/inventory/    per-sector supply inventories, one CSV per sector
docs/              CLASSIFICATION_RULE.md, METHODOLOGY.md, DATA_DICTIONARY.md, MEMO.md
outputs/           gap index, validation results, maps
powerbi/           star schema CSVs, measures.dax, BUILD_GUIDE.md
src/               one script, one job
```

**`data/inventory/` is not all hand-scored.** Schools are `manual`. Every
other sector is `assignment_method = derived`: applied by code to frozen
evidence and exactly reproducible. See `docs/CLASSIFICATION_RULE.md` 6.1.

### Scripts

| Script | Does | Note |
|---|---|---|
| `fetch_ospi.py` | Downloads OSPI language data | Skips if already on disk |
| `explore_ospi.py` | Inspects it | Read-only |
| `build_demand.py` | Filters to six districts, checks suppression | |
| `apply_crosswalk.py` | Normalises language names, writes demand table | |
| `build_inventory_skeleton.py` | Generates blank inventory rows | **Overwrites the inventory. Never rerun after scoring.** |
| `show_inventory.py` | Reads the inventory | Read-only, exists so nobody runs the skeleton script to look at data |
| `build_gap_table.py` | Joins demand to supply, scores gaps | Weights are constants at the top |
| `check_key.py` | Diagnoses the Census API key | |
| `fetch_census.py` | C16001 at tract level | |
| `fetch_b16001_puma.py` | B16001 at PUMA level | Kept as evidence for the negative result |
| `fetch_pums.py` | PUMS person records, five PUMAs | |
| `fetch_districts.py` | C16001 at school district level | |
| `validate_apportionment.py` | The Phase 2 test | |
| `fetch_kingcounty_sitemap.py` | Freezes kingcounty.gov sitemap URLs | |
| `probe_agency_sites.py` | Reusable site profiler, all sectors | Do not write new fetchers per sector |
| `audit_kingcounty_locales.py` | Tests the 7 County locale paths for real content | Skips if output on disk |
| `build_kcls_inventory.py` | Library sector | `derived` |
| `build_transit_inventory.py` | Transit sector | `derived` |
| `build_city_inventory.py` | City sector | `derived`, holds the widget/pathway rule |
| `build_legal_inventory.py` | Legal aid sector | `derived` |
| `build_food_inventory.py` | Food assistance sector | `derived` |
| `build_health_inventory.py` | Health sector | `derived` |
| `build_master_inventory.py` | Concatenates all sectors, assigns scope and `tier_verified` | |
| `build_city_district_crosswalk.py` | City-to-district area overlap | Feeds the reach weights |
| `build_gap_index.py` | Phase 4 gap index, two readings | **Tuning constants at the top** |
| `build_access_map_layers.py` | Service points and access deserts | |
| `compare_kc_tier_map.py` | Demand vs King County Appendix C | Memo's central exhibit |
| `sensitivity_analysis.py` | Sweeps 11 scenarios | Must run from repo root |
| `build_powerbi_model.py` | Writes the star schema to `powerbi/` | |

---

## Conventions that exist for a reason

**Read raw data as strings first.** `pd.read_csv(..., dtype=str)`. Suppressed cells contain words, not numbers. Number mode turns them into blanks silently and you never learn what you lost.

**Freeze every download.** Raw API responses go to `data/raw/` and the script skips re-downloading. Sources revise their published data. Without a frozen copy you cannot tell whether a changed number came from your code or from theirs.

**Announce what you exclude, never drop silently.** Unresolved languages, unscored rows, unmapped codes. Count them, print them, and report the count. A total that does not reconcile is worse than a smaller total that does.

**Never count PUMS rows. Sum `PWGTP`.** Each record carries a sampling weight and represents many people. Counting rows gives plausible-looking numbers that are wrong by a factor of twenty.

**Wrap every API decode.** The Census answers some bad requests with a plain-text sentence and an HTTP 200. `resp.json()` then raises a JSON error that says nothing about the real problem. Catch it and print the body and the URL.

**Quote free-text CSV fields.** The `notes` and `reason` columns are prose and contain commas.

**Scripts that write and scripts that read stay separate.** Reading data should never require running something that destroys it.

**Tuning constants live at the top of the file.** The gap index weights are there specifically so the Phase 4 sensitivity analysis can sweep them without touching logic.

---

## Known weaknesses, stated so nobody rediscovers them as surprises

1. **Single coder.** Every judgment call in the project comes from one person with no inter-rater reliability statistic. This matters less than it did at Phase 1: schools are still `manual`, but every other sector is `derived`, applied by code to frozen evidence. What remains subjective is the rule itself and the `quality_verdict` readings. A blind re-score of a 10-row sample would still be cheap and has not been done.
2. **Inventory depth.** Most districts were assessed from one or two pages. A reviewer could reasonably ask whether translated documents exist on a subpage nobody opened. The eleven severity-1.00 rows are the ones the memo will name and deserve a deeper pass plus archived evidence URLs.
3. **Web inventory understates reality by design.** Services that exist but are not advertised online score as absent. Deliberate, per the pathway rule, but it is a bias.
4. **Uneven assessment quality across languages.** Elias can judge whether Amharic text was human-written. For Chuukese or Punjabi the judgment rests on file type and provenance.
5. **OSPI covers only families with school-age children.** This is the strongest alternative explanation for the Phase 2 error and the reason Test A exists.

6. **Demand and supply are measured on different populations.** Provision covers 51 agencies in seven sectors. Family counts come only from OSPI. So a count attached to a food bank or a clinic is still a count of households with a K-12 student. Households without school-age children are absent from every number in this project. Read every family count as a floor.

7. **OSPI records home language, not English proficiency.** King County's tier map ranks Limited English Proficiency population. The two are not interchangeable, and no claim in this project maps one onto the other. Where the memo puts them side by side it says so at the table.

### Found in review, 2026-09-18. Not yet fixed.

8. **`local_cut` moves with the sensitivity scenario.** In `build_gap_index.py`, `local_cut = scope_weight["city"] * 0.5`. When a scenario changes the city weight, the definition of "local" moves with it, so `families_no_local_document` is not comparable across scenarios even though `sensitivity_analysis.py` prints it side by side as if it were. Under `scope_flat_all_equal` the cut becomes 0.5 and county agencies at weight 1.0 start counting as local. The gap-score ranking result is unaffected; the local-document measure is. **That measure is on Power BI page 1.**

9. **`scope_weight["district"]` is dead code.** The district weight is hardcoded to 1.0 at the reach step. So `scope_steep_local_only` and `scope_flat_all_equal` do not actually sweep the school sector, which is the only district-scope sector.

10. **No school row can ever be `verified_human`.** `build_master_inventory.py` blanks `quality_verdict` for schools, and `tier_verified` is derived from it. Every school tier-3 claim is therefore permanently `unverified` and permanently demoted in the conservative reading. Schools are the only weight-1.0 sector, so the most locally relevant provision is structurally penalised and no amount of verification work can change it without a code change.

11. **The sensitivity numbers in the docstring are prose, not assertions.** `sensitivity_analysis.py` states its results in the module docstring. Nothing recomputes or checks them. If the data changes they go stale silently.

12. **The conservative reading never touches oral tiers.** `unverified_tier3_as` is applied to `written_tier` only. An unverified oral tier 3 is trusted in both readings, so the harsh case is understated.

---

---

## The upstream fix, and why it matters for the memo

OSPI already publishes **Multilingual Family Communication Templates in 40+ languages**, free, for any district to use:

https://ospi.k12.wa.us/student-success/access-opportunity-education/migrant-and-multilingual-education/multilingual-education-program/multilingual-family-communication-templates

Verified as including **Amharic, Tigrinya, Pashto, Dari, Farsi, Arabic, French, Somali, Punjabi, Ukrainian, Marshallese, Karen, Khmer** and others.

The templates are not marketing leaflets. They cover **Home Language Surveys, program placement notices, continued-eligibility and exit letters, WIDA testing notifications, and ELD program waiver forms.** Those are the consequential documents.

**Every one of the languages scoring written_tier 0 in the Phase 1 inventory has a template already published.**

This is the single most important framing asset in the project. It converts the finding from "there is a gap" into "there is a gap, the fix already exists upstream, it is free, and it is not being used." A memo that says the first thing gets filed. A memo that says the second thing is actionable.

Preserve this framing in the memo and the README. Do not let the recommendation soften into "districts should consider improving language access."

### A related finding worth keeping

Highline's translation widget is Google Translate **restricted to 7 languages**: Dari, Ukrainian, Vietnamese, Spanish, Thai, Russian, Somali.

The unrestricted default covers 135+. So Highline actively configured its tool to serve fewer languages than it shipped with, and the excluded set includes Amharic (164 families) while the included set contains Thai (35 families across all six districts).

Highline's own homepage names Amharic, Punjabi, Arabic and Khmer among its most common family languages. None of those four are in its widget. Its board Policy 4218 promises free translation of vital documents in any language, and an Amharic-reading parent has no way to discover that promise exists.

That contradiction, inside one district's own website, is the sharpest single example in the dataset.

## The exemplar, and why it matters more than any single gap

**Washington Healthplanfinder** is the reference case for what adequate looks like. Native-speaker verdict on its Amharic, 2026-09-07: *"translated perfectly, surprisingly good, an example for everyone."*

It publishes **26 languages**, each with genuine in-language text, a translated PDF, and the support number **1-855-923-4633** explained in that language. Amharic, Dari, Tigrinya, Oromo, Pashto, Punjabi, Khmer, Lao, Somali, ASL.

Compare **DSHS form 14-001**, the food assistance application: **12 languages**. Same state, largely the same clients.

**Use this in the memo.** Every other finding in the project describes a failure, and a failure can always be answered with "this is hard." The exemplar removes that answer. A Washington State agency, same budget rules, same residents, same languages, does it well. The gaps are therefore choices, not constraints.

### The verification ratio

Four Amharic offerings have been read by a native speaker:

| Agency | Verdict |
|---|---|
| Washington Healthplanfinder | human, exemplary |
| City of Burien | human |
| King County | **machine** |
| Eastside Legal Assistance Program | **machine** |

**Two of four named Amharic offerings were machine output.** That ratio is how every unverified tier 3 in this dataset should be read, and it belongs in the README.

## The memo recipient: decided 2026-09-07

**King County Language Access Program**, Office of Equity and Social Justice.
Intake: `kcla@kingcounty.gov`, 206-477-6608.

**Why them, and not OSPI or a city.** They administer **King County Code Chapter 2.15**, which is law, not policy. KCC 2.15.030.B requires every King County agency to hold a Language Assistance Plan covering *"translation of webpages, automated phone messages, and informational signage"* into the County's top six languages, based on the County's tier map.

The findings land on that clause by clause:

| KCC 2.15.030.B requires | Measured in this project |
|---|---|
| translation of **webpages** | Seven King County locale paths (`/es-ES`, `/so-SO`, …) serve English content; 71 of 77 sampled pairs carry main-content text identical to English after stripping chrome and markup. Its Amharic is machine translation, native-speaker verified. |
| **automated phone messages** | Metro's interpreter line is option 1 on the general call centre number, advertised in English only, and closed weekends and holidays. |
| informational signage | **Not measurable by this method. Say so explicitly.** |

So the ask is not "please care." It is "here is a measured compliance gap in your own code, with evidence URLs."

### What this scopes IN and OUT, stated honestly

King County has authority over **Metro, Public Health, DCHS, DJA** and county contractors. It does **not** control the six school districts, the eight cities, DSHS, or WashingtonLawHelp.

So the memo structure is:
1. **Lead with King County's own agencies.** These are the compliance findings.
2. **Use the other sectors as regional context**, showing the county is neither an outlier nor a leader.
3. **Close with Washington Healthplanfinder as the model**, deliberately a *state* agency so the comparison is not a peer insult, and one whose Amharic a native speaker called exemplary.

### Phase 4 tasks this creates

- ~~**Find the County's "tier map" and its top six languages.**~~ **Found.** Appendix C of INF-14-2-AEO, frozen at `data/raw/kingcounty_language_tiers_appendixC.pdf`. Twenty languages total: Spanish alone at tier 1, eight at tier 2, eleven at tier 3. Dari, Pashto and Marshallese appear nowhere on it. Joined to demand by `src/compare_kc_tier_map.py`.
- **Locate published Language Assistance Plans** for Metro and Public Health. KCC 2.15.030.B requires them to exist.
- Rank the gap index with King County agencies separable from the rest.

## Open items

- **Preempt the Dari/Farsi objection in the memo.** Farsi is tier 3 on the map; Dari is absent. The first defence of the tier map will be that Dari speakers are served by Farsi materials. The answer is in the data: Farsi is 328 families, Dari is 3,040. A tier assigned on 328 people would be covering 3,368. Raise it before someone else does.
- Archive evidence URLs at web.archive.org for the rows the memo names.
- `DATA_DICTIONARY.md` is v1.0 and documents only Phase 1 to 3 tables. It covers none of the star schema: `fact_gap`, `fact_provision`, `fact_access_desert`, `dim_language`, `dim_agency`, `dim_district`, `fact_service_point`, `bridge_point_language`. The memo attaches "a public dataset" and half of it has no dictionary.
- Bring `school_inventory.csv` onto the library schema: add `agency_id` and `assignment_method='manual'`. Additive, no rescoring.
- Power BI pages 3 and 4, then publish to Service.
- No README yet. No GitHub remote yet.
