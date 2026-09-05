# Language Support Classification Rule

**Project:** Language Access in South King County
**Version:** 2.0
**Status:** Written before inventory collection began. Any change after collection starts must be logged in the Revision Log at the bottom and re-applied to all prior entries.

---

## 1. Why this document exists

Assigning a language-support level to an agency is a judgment call made 200 to 300 times. If the rule lives only in the analyst's head, the resulting dataset is an opinion survey.

The standard this rule has to meet: **two people applying it to the same website should land on the same tier.** Where that is not achievable, the ambiguity is recorded rather than resolved silently.

---

## 2. Unit of observation

One row per **(agency, language)** pair.

An agency serving 8 languages produces 8 rows, not 1. The tier is assigned per language, never to the agency as a whole. "This district supports 8 languages" is a summary statistic, not an observation.

---

## 3. The four tiers

| Tier | Name | Test |
|---|---|---|
| **3** | Human-translated materials | At least one family-facing document exists in this language, produced or reviewed by a human. |
| **2** | Interpretation or translation on request | A human service can be requested in this language, **and** the request pathway is reachable by someone who reads only this language. See §4. |
| **1** | Machine translation only | Automated translation of web page text is available in this language. No human-produced materials, no reachable request pathway. |
| **0** | Nothing | The language is not offered, not listed, and there is no way to request service in it. |

**Tiers are a ceiling, not a sum.** An agency with human-translated documents is Tier 3 even if it also has a Google Translate widget. Record the highest level reached.

### 3.1 Modes

A tier is assigned per **mode**, never once for an agency.

| Mode | Column | Question it answers |
|---|---|---|
| Written | `written_tier` | Has the agency communicated with this community in writing, in their language? |
| Oral | `oral_tier` | Can a speaker of this language talk to a human at this agency? |
| Collection | `collection_tier` | Can a speaker of this language borrow material in it? |

The written and oral split exists because a document and an interpreter serve different people. Renton publishes documents in "Chinese" without naming a variety: written Chinese serves both Cantonese and Mandarin readers, an interpreter does not.

`collection_tier` was added in v2.0 for the library sector. It is null for sectors that hold no collections, which is most of them. Its scale is deliberately not the full 0 to 3:

| Value | Meaning |
|---|---|
| 3 | Materials held for all ages |
| 2 | Children's materials only |
| 1 | **Not used.** There is no machine-translated book. |
| 0 | No materials in this language |

**Do not merge `collection_tier` into `written_tier`.** See §5.7.

---

## 4. The request-pathway rule

This is the most consequential decision in the project.

Most agencies publish some version of "interpreters available in any language on request." Taken at face value, this makes every agency Tier 2 in all 193 languages, and the analysis returns no findings.

**The rule:**

> Tier 2 requires that the request pathway itself be communicated in that language.

**Reasoning.** A parent who reads only Amharic, facing an English-only page that explains how to request an Amharic interpreter, has not been given access. The service exists on paper and is unreachable in practice. A service you cannot find out about is not a service.

**What satisfies the pathway requirement (any one):**

- The request instructions appear in that language on the site
- A phone number is published with in-language voice prompts or an in-language line
- The language appears on a physical or digital "point to your language" card the agency publishes

**What does not satisfy it:**

- An English-only page stating interpreters are available in any language
- A generic contact form in English
- The agency having an interpreter contract that is not advertised to families

**Consequence, stated honestly:** this rule will score some agencies lower than their actual internal capacity. That is the intended reading. The project measures access as families experience it, not capacity as agencies report it. This is recorded in the limitations section of the final writeup.

---

## 5. Decided edge cases

Each of these was hit during Phase 1 and resolved. Additions go here with the date and the reasoning.

### 5.1 Google Translate widget with a curated language list

**Decision: Tier 1.**

A restricted language list makes the widget look like a deliberate service. It is not. The output is machine-generated, the agency disclaims its accuracy, and the language list reflects a configuration choice, not a translation investment.

*Observed at Highline Public Schools, whose own disclaimer states machine translation "does not approach the fluency of a native speaker" and "should not be considered exact."*

### 5.2 PDFs and attached documents under a machine widget

**Decision: do not count toward any tier.**

Machine translation widgets translate HTML page text only. Attached files stay in the source language. Highline's own notice confirms this: "some files or items cannot be translated, including graphs, photos, and other file formats."

This matters because the consequential documents, enrollment forms, discipline notices, special education placement letters, are almost always attachments. A site can appear fully translated while every document that carries legal weight remains English-only.

### 5.3 A single translated document

**Decision: Tier 3, with depth recorded separately.**

One human-translated document meets the Tier 3 test. Overloading the tier with a volume judgment would make it subjective and unreproducible.

Instead, each Tier 3 row records `translated_doc_count` and `translated_doc_types`. Depth becomes a separate, measurable dimension available to the gap index rather than a hidden assumption inside the tier.

### 5.4 Third-party interpreter phone lines

**Decision: Tier 2 if advertised to families, subject to §4.**

A contracted service (LanguageLine or similar) is a real human service. It counts only if a family could discover it, which returns to the request-pathway rule.

### 5.5 An agency naming a language on one page and not offering it on another

**Decision: score the offering, not the claim.**

Highline's homepage names Amharic among its most common family languages. Amharic does not appear in its translation picker. The tier reflects what is provided, not what is acknowledged.

The discrepancy is recorded in the row's notes field, because it is itself a finding: the agency already knows about the need.

---

### 5.6 Signed languages

**Decision: apply §4 by the language's own modality, and flag the row.**

American Sign Language has no written form. The §4 pathway test asks whether request instructions are readable in the language, which cannot be satisfied for ASL on any website.

Reading the rule literally would score every agency 0 for ASL, including agencies that name ASL explicitly and provide it. That is a rule artefact, not a finding.

For a signed language, the pathway test is satisfied by the agency **naming the language explicitly** as an available service. The row carries a note recording that §4 was applied in modified form.

*Observed at KCLS, which names ASL among the five languages available whenever a branch is open.*

### 5.7 Borrowable collections are not agency communications

**Decision: `collection_tier`, never `written_tier`.**

A library holding Amharic novels has not written anything to Amharic-speaking families. It has bought books. Both are real services and they are not the same service.

Scoring collections as `written_tier = 3` would make "written tier 3" mean a translated enrollment form at a school district and a shelf of picture books at a library branch. The cross-sector comparison, which is the point of Phase 3, would then be comparing nothing.

*Consequence at KCLS: 17 languages reach collection tier 3, while only 9 have any translated page at all, and for 8 of those 9 the sole translated page is the interpreter request page itself.*

### 5.8 An agency with no machine translation widget cannot score tier 1

**Decision: score 0, not 1.**

Tier 1 requires automated translation of page text to be available. An agency running no widget offers none. A language with no in-language pathway at such an agency scores 0.

This is worth stating because it inverts the usual reading. A widget looks like a floor under an agency's score, so the agency without one scores lower for languages it may genuinely serve by phone.

*Observed at KCLS, which runs no widget anywhere on its site and contracts phone interpreting in 240+ languages. Nine languages have an in-language request page and score oral tier 2. The rest score 0, because a speaker has no published route to discover a service that demonstrably exists for them.*

### 5.9 Depth belongs in its own column, not in the tier

**Decision: extend the row, never the scale.**

The same pattern as §5.3. When a service varies in depth, record the depth beside the tier rather than inventing intermediate tiers.

Added in v2.0:

| Column | Values | Records |
|---|---|---|
| `oral_locations_phone` | count | Locations offering phone interpreting |
| `oral_locations_video` | count | Locations offering video or audio interpreting |
| `oral_availability` | `always`, `weekdays` | Whether the language is available whenever the agency is open |
| `translated_page_count` | count | Distinct translated pages found |
| `collection_branches` | count | Branches holding material in this language |

*Observed at KCLS: video and audio interpreting reaches 20 of 22 study-area locations, phone reaches all of them, and only five languages are available outside weekday hours. Three facts, one tier.*

### 5.10 A page exists in the language but a native speaker judges it poor

**Decision: record the verdict in a separate column. Do not change the tier.**

This looks wrong at first, so the reasoning matters.

The tier 3 test is "human-produced or reviewed." A native speaker reporting that a page reads as unreviewed machine output is direct evidence that the test is not met, and the instinct is to downgrade the row to tier 1.

**Downgrading would introduce a worse bias than it removes.** Quality can only be judged in languages someone on the project can read. In practice that is Amharic. Every other language is scored on structural signals: does a page exist, is it human-produced, is it a real translation rather than an English page under a translated title.

If poor-quality Amharic is downgraded while unverifiable Punjabi, Khmer and Marshallese pages keep tier 3, then **the one language subject to expert scrutiny is punished for being scrutinised.** The dataset would systematically understate provision in exactly the language the analyst can read, and a reviewer comparing Amharic against Punjabi would be comparing two different standards.

**The rule:**

> Quality verdicts are recorded in `data/inventory/quality_checks.csv` and surfaced as a `quality_verdict` column. Tiers stay as structurally assigned. Phase 4 reports the gap index both ways, unadjusted and quality-adjusted, as a sensitivity test.

That keeps a real finding visible without letting uneven verification silently distort the ranking.

**Verdict values:** `human`, `poor`, `machine`, `unchecked`.

*First application, 2026-09-05, both by native-speaker review:*

| Agency | Language | Verdict |
|---|---|---|
| City of Burien | Amharic | `human`, genuine translation of consequential documents |
| King County | Amharic | `poor`, "not direct translations and not well translated" |

Burien's Amharic pages cover the public safety levy, immigration resources and emergency information. Those are consequential documents in the same category as the school placement letters this project is built around, and no school district in the study area publishes their equivalent in Amharic.

**This is the honest scope of the finding:** two agencies, one language, checked by one reader. It is worth more than it looks, because it is the only direct evidence in the project that structural detection and actual quality can disagree. It is also a reminder that every unchecked tier 3 row in this dataset carries the same unmeasured risk.

---

## 6. Evidence required per row

No tier is assigned without a record supporting it.

| Field | Description |
|---|---|
| `agency_name` | Full official name |
| `sector` | schools, health, food, city, library, legal, transit |
| `language` | Canonical name from `language_crosswalk.csv` |
| `tier` | 0, 1, 2, or 3 |
| `evidence_url` | The specific page the tier was assigned from, not the homepage |
| `capture_date` | Date observed |
| `translated_doc_count` | Tier 3 only |
| `translated_doc_types` | Tier 3 only, e.g. enrollment, health, discipline, special education |
| `pathway_in_language` | Boolean, whether §4 was satisfied |
| `notes` | Ambiguity, contradictions, anything a reviewer should see |
| `assigned_by` | Analyst initials, in case a second coder is added |
| `assignment_method` | `manual` or `derived`. See below. |

### 6.1 Manual and derived assignment

Added in v2.0.

Some agencies publish their language provision as structured data. Where that is true, the rule is applied **by code against a frozen copy of that data**, and the row is marked `assignment_method = derived`.

A derived row is stronger evidence than a hand-scored one, because rerunning the script reproduces the score exactly and the judgment is visible in the source. It removes the single-coder problem (§7.3) for that sector.

A derived row is only as good as the mapping from the agency's language labels to canonical names. Those mappings live in a reference file with a stated reason per row, for example `data/reference/kcls_language_map.csv`, and are reviewable independently of the code.

### 6.2 Rows are keyed by agency, not by geography

Phase 1 rows were `(district, language)` and carried a `families` count, because OSPI reports demand by district and each district is its own agency.

From Phase 3 the two stop coinciding. King County Library System is one agency across 22 study-area locations and six school districts. There is no families count that belongs on a KCLS row.

Therefore:

- The inventory holds supply only. No demand column.
- Physical sites live in a separate locations table, with coordinates, and are joined to districts by point-in-polygon against Census TIGER unified school district polygons.
- Demand meets supply in Phase 4, by geography, deliberately and once.

**Do not filter locations by city name.** School district boundaries do not follow city boundaries anywhere in this study area. Four KCLS branches carry a Seattle mailing address while sitting in Highline or Renton school districts, and one of them, Skyway, is one of only two branches in the county holding Amharic material.

**Capture date is mandatory.** Websites change. Without it, the dataset cannot be reproduced or defended six months from now.

---

## 7. Known limitations of this rule

Stated up front rather than discovered by a reviewer.

1. **Web inventory understates reality.** Services that exist but are not advertised online are scored as absent. This is a systematic downward bias and it is deliberate, per §4, but it is a bias.

2. **Uneven assessment quality across languages.** The analyst can evaluate whether Amharic text was human-written. For Chuukese, Marshallese, or Punjabi, that assessment relies on structural signals such as file type and provenance rather than direct reading. Confidence is therefore not uniform across rows.

3. **Single coder.** All rows are assigned by one person. No inter-rater reliability statistic is available. The rule is written to make a second coder possible; none has been run.

4. **Point-in-time snapshot.** Each row reflects one date. The dataset is a photograph, not a monitor.

5. **Absence is evidenced by sitemap, not by browsing.** A written tier of 0 means no translated page appears in the agency's own sitemap. A translated PDF sitting in a media library, unlinked from any page, would not be found. This is a downward bias of the same family as §7.1.

6. **Derived rows inherit the agency's own errors.** KCLS states its collections twice on one page and contradicts itself in three places, recorded in `outputs/kcls_source_disagreements.csv`. Derived scoring propagates such contradictions rather than resolving them, which is correct, but it means a derived row is not automatically more accurate than a hand-scored one. It is more *reproducible*.

---

## Revision Log

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-09-02 | Initial rule, written before inventory collection began. |
| 2.0 | 2026-09-03 | Phase 3, library sector. Added §3.1 modes and the `collection_tier` column; §5.6 signed languages; §5.7 collections are not communications; §5.8 no widget means tier 0, not tier 1; §5.9 depth columns; §6.1 manual and derived assignment; §6.2 agency-keyed rows and the city-name warning; limitations 5 and 6. |

**Note on versioning.** Before this entry the document header read 1.0 while the project notes referred to the rule as v2.0, and the log held only the 1.0 entry. No record of an intermediate revision survives. This entry sets the header and the log to 2.0 and describes only changes that can be verified in the current file. If a v1.x revision did occur, its content is not recoverable from the repository and is treated as lost rather than reconstructed from memory.
