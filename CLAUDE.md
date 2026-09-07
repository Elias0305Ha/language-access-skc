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

**Headline result: 1,428 families have no written provision in their language.** Eleven district-language pairs score a flat 1.00 severity, meaning nothing written and nothing oral. Highline owns five of them.

### Phase 2: complete

Census integration and the apportionment validation.

**Result: apportionment fails.** Mean absolute error 7.1 percentage points across 219 district-language rows, confirmed independently inside PUMS. Auburn's Marshallese share was predicted at 7.5% and is actually 63.1%.

Written up in `docs/METHODOLOGY.md`.

### Phase 3: in progress, 3 of 6 sectors done

**RESUME HERE: legal aid is the next sector.** Add its agencies to the
`AGENCIES` list in `src/probe_agency_sites.py` and run it, then write
`src/build_legal_inventory.py` modelled on `build_city_inventory.py`.
The profiler is reusable; do not write new fetchers per sector.

Multi-sector supply inventory. **All seven sectors**, sequenced cheapest first:

1. ~~Library (King County Library System)~~ **done, 2026-09-03**
2. ~~Transit (King County Metro, Sound Transit)~~ **done, 2026-09-05**
3. ~~City government (eight cities)~~ **done, 2026-09-05**
4. Legal aid
5. Food assistance
6. Health clinics (most decentralised, most expensive, goes last)

Ships the public dataset on GitHub with a data dictionary.

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

### Phases 4 and 5

Geocoding, distance analysis, access deserts, gap index, sensitivity analysis. Then Power BI, memo, README, publish.

---

## Decisions already made. Do not silently revisit these.

**Study area is six districts.** Charter and tribal schools excluded, noted as a limitation.

**Tiers are assigned per (agency, language) pair, in two modes.** `written_tier` and `oral_tier`, each 0 to 3. Never one tier for an agency as a whole. The mode split exists because Renton publishes documents in "Chinese" without naming a variety: written Chinese serves both Cantonese and Mandarin readers, interpreters do not.

**Tier 2 requires that the request pathway be reachable in that language.** An English-only page saying interpreters are available in any language does not count. This is the most consequential rule in the project. Full reasoning in `docs/CLASSIFICATION_RULE.md` section 5.

**Machine translation counts for discovery, not for documents.** A Google Translate widget can satisfy the pathway test (someone can find the email address) but never produces tier 3 (it cannot translate PDFs).

**Consequence to remember:** an unrestricted Google Translate widget covers 135+ languages, so tier 2 becomes nearly free for any agency running the default. Tier 2 does not discriminate. The gap index therefore weights the 2-to-3 step more heavily than 0-to-2.

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
data/inventory/    the supply inventory, hand-scored
docs/              CLASSIFICATION_RULE.md, METHODOLOGY.md
outputs/           gap index, validation results, maps
src/               one script, one job
```

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

1. **Single coder.** All 60 tier assignments come from one person with no inter-rater reliability statistic. A blind re-score of a 10-row sample would fix this cheaply and has not been done.
2. **Inventory depth.** Most districts were assessed from one or two pages. A reviewer could reasonably ask whether translated documents exist on a subpage nobody opened. The eleven severity-1.00 rows are the ones the memo will name and deserve a deeper pass plus archived evidence URLs.
3. **Web inventory understates reality by design.** Services that exist but are not advertised online score as absent. Deliberate, per the pathway rule, but it is a bias.
4. **Uneven assessment quality across languages.** Elias can judge whether Amharic text was human-written. For Chuukese or Punjabi the judgment rests on file type and provenance.
5. **OSPI covers only families with school-age children.** This is the strongest alternative explanation for the Phase 2 error and the reason Test A exists.

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
| translation of **webpages** | Seven King County locale paths (`/es-ES`, `/so-SO`, …) serve English content; 71 of 77 sampled pairs byte-identical to English. Its Amharic is machine translation, native-speaker verified. |
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

- **Find the County's "tier map" and its top six languages.** If the top six do not match measured need in South King County, that is a finding against the ordinance's own benchmark. Not yet located; not on the language access page or in the sitemap.
- **Locate published Language Assistance Plans** for Metro and Public Health. KCC 2.15.030.B requires them to exist.
- Rank the gap index with King County agencies separable from the rest.

## Open items

- Archive evidence URLs at web.archive.org for the rows the memo names.
- `DATA_DICTIONARY.md` written 2026-09-05. Keep it current as each sector lands.
- Bring `school_inventory.csv` onto the library schema: add `agency_id` and `assignment_method='manual'`. Additive, no rescoring.
- No README yet.
