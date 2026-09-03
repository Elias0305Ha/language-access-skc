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

### Phase 3: next

Multi-sector supply inventory. **All seven sectors**, sequenced cheapest first:

1. Library (King County Library System is one organisation covering many branches)
2. Transit (King County Metro, Sound Transit)
3. City government (eight cities)
4. Legal aid
5. Food assistance
6. Health clinics (most decentralised, most expensive, goes last)

Ships the public dataset on GitHub with a data dictionary.

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

## Open items

- Pick the memo recipient. King County Office of Equity and Social Justice, OSPI's multilingual education office, a city council, or a nonprofit. This changes which numbers lead and should be decided before Phase 4 finishes.
- Archive evidence URLs at web.archive.org for the rows the memo names.
- `DATA_DICTIONARY.md` does not exist yet. Phase 3 ships it.
- No README yet.
