# Language Support Classification Rule

**Project:** Language Access in South King County
**Version:** 1.0
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

**Capture date is mandatory.** Websites change. Without it, the dataset cannot be reproduced or defended six months from now.

---

## 7. Known limitations of this rule

Stated up front rather than discovered by a reviewer.

1. **Web inventory understates reality.** Services that exist but are not advertised online are scored as absent. This is a systematic downward bias and it is deliberate, per §4, but it is a bias.

2. **Uneven assessment quality across languages.** The analyst can evaluate whether Amharic text was human-written. For Chuukese, Marshallese, or Punjabi, that assessment relies on structural signals such as file type and provenance rather than direct reading. Confidence is therefore not uniform across rows.

3. **Single coder.** All rows are assigned by one person. No inter-rater reliability statistic is available. The rule is written to make a second coder possible; none has been run.

4. **Point-in-time snapshot.** Each row reflects one date. The dataset is a photograph, not a monitor.

---

## Revision Log

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-09-02 | Initial rule, written before inventory collection began. |
