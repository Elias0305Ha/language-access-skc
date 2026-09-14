# Power BI build guide

Everything here is clicks in Power BI Desktop. The data model is already built in
`powerbi/*.csv`. Power BI Desktop is free from the Microsoft Store; you need a
work or school account only for the final publish step.

Work through the sections in order. Sections 1 to 4 are setup. Section 5 is the
report itself.

---

## Why the report looks the way it does

Two rules drive every choice below, and they are worth being able to explain in
an interview because most dashboards get them wrong.

**Pick the form from the data's job, not from what looks impressive.** A single
important number is a stat tile, not a gauge. A ranking is a bar chart, not a pie.
A compliance list is a table, and a table is the right answer sometimes.

**Colour comes last, and it is assigned by job.** Magnitude gets one hue, light to
dark. Identity gets a fixed set of hues in a fixed order. Never a rainbow for
magnitude, never a second y-axis, never a colour that changes meaning between
pages.

The three identity colours used here were run through a colourblind-safety
validator rather than chosen by eye:

| Role | Hex | Used for |
|---|---|---|
| Identity 1 | `#2a78d6` blue | in-language document |
| Identity 2 | `#eb6834` orange | machine widget only |
| Identity 3 | `#1baf7a` aqua | no pathway |

Worst-case colourblind separation ΔE 9.2, normal-vision 24.0, both above the
required floors. The aqua sits below 3:1 contrast on a white surface, so
**anything drawn in aqua must carry a visible data label.** That is not optional
styling; it is what makes the chart readable for everyone.

For magnitude (families, gap score, tier level) use a **single blue hue, light to
dark**. Power BI calls this a diverging/sequential setting under
*Format visual → Colours → Conditional formatting → Gradient*. Use the gradient
with only a minimum and maximum colour, no middle colour.

---

## 1. Load the data

1. Open Power BI Desktop → **Blank report**.
2. **Home → Get data → Text/CSV**.
3. Load all eight files from `powerbi/`:

```
dim_language.csv          dim_agency.csv          dim_district.csv
fact_provision.csv        fact_gap.csv            fact_access_desert.csv
fact_service_point.csv    bridge_point_language.csv
```

For each, click **Transform Data** rather than Load the first time, so you can
check the column types, then **Close & Apply**.

## 2. Fix the data types

Power BI guesses types and gets some wrong. In **Model view**, check these:

| Table | Column | Type |
|---|---|---|
| `fact_service_point` | `lat`, `lon` | Decimal Number |
| `fact_gap` | `families`, `gap_score`, `severity` | Decimal Number |
| `fact_provision` | `written_tier`, `oral_tier` | Whole Number |
| `dim_language` | `families_total` | Whole Number |
| `fact_access_desert` | `is_access_desert` | True/False |

Then set the geography hints so the map works: select `fact_service_point[lat]`
→ **Column tools → Data category → Latitude**. Same for `lon` → **Longitude**.

## 3. Build the relationships

**Model view → drag field to field.** All are one-to-many, single direction,
from the dimension to the fact.

```
dim_language[language]           1 -> *  fact_provision[language]
dim_language[language]           1 -> *  fact_gap[language]
dim_language[language]           1 -> *  fact_access_desert[language]
dim_language[language]           1 -> *  bridge_point_language[language]
dim_agency[agency_id]            1 -> *  fact_provision[agency_id]
dim_agency[agency_id]            1 -> *  fact_service_point[agency_id]
dim_district[district]           1 -> *  fact_gap[district]
dim_district[district]           1 -> *  fact_access_desert[district]
fact_service_point[location_id]  1 -> *  bridge_point_language[location_id]
```

**The bridge is the one to understand.** A library branch holds several language
collections, and a language is held at several branches. That is a many-to-many,
and Power BI handles it badly if you try to join the two tables directly. The
bridge table sits between them so both sides stay one-to-many. If an interviewer
asks you one modelling question, it will be this one.

## 4. Add the measures

**Home → New measure**, then paste one measure at a time from
`powerbi/measures.dax`. Put them all in `fact_gap` so they are easy to find.

Set formatting as you go: `Unverified Tier 3 Share` and
`Share Where Translation Is Optional` are percentages; the family counts are
whole numbers with a thousands separator.

---

## 5. The report, four pages

### Page 1 — "What the data says"

The job of this page is one honest headline. Four stat tiles across the top, one
chart below.

**Stat tiles** (visual type: **Card**). No chart, because a single number does not
need a plot.

| Card | Measure | Shows |
|---|---|---|
| Families measured | `Families in Selection` | 36,775 |
| No written provision anywhere | `Families With No Written Provision` | 393 |
| No local translated document | `Families With No Local Document (Optimistic)` | 1,760 |
| Tier-3 claims never read | `Verification Status` | 153 of 155 |

**Do not put `No Local Document Range` on a card.** It reads
*"1,760 to 36,611 families"*, which is 5% to 99.6% of the study population. A
range that wide does not communicate care, it communicates that nothing is
known, and it hides the mechanism that produces it.

The two facts it was trying to compress are different kinds of thing, so give
each its own card. Card three is a **measurement**: if every claim of a
translated document is accurate, 1,760 families still have none locally. Card
four is an **uncertainty**: almost none of those claims has been checked.

Then one text box, directly beneath, saying how they connect:

> 153 of the 155 claimed human-translated documents have never been read by
> someone who reads that language. Of the four that were checked, two turned out
> to be machine translation. If unverified claims are set aside entirely, the
> 1,760 figure rises to 36,611.

That paragraph is the honest version. It gives the reader the low number, the
reason to doubt it, and the high number, in that order, and it stays legible.

**Chart** (visual type: **Clustered bar chart**, horizontal):
- Y axis: `dim_language[language]`
- X axis: `Families`
- Filter: Top 15 by `Families`
- Colour: single blue, no gradient needed since it is one series
- Turn **Data labels on**

Sort descending by families. A bar chart, not a pie, because the job is ranking.

**Slicer**: `dim_district[district]`, one row across the top.

### Page 2 — "The ordinance" (this is the memo's exhibit)

The job here is a compliance list, so the main visual is a **table**. That is the
correct form; do not make it a chart.

**Table** with columns:
- `dim_language[language]`
- `Families`
- `dim_language[kc_status]`
- `dim_language[kc_tier]`

Sort by `Families` descending. Then **conditional formatting on `kc_status`**:
background colour by rule, `NOT ON THE TIER MAP` in a light red, everything else
plain. Rules, not a gradient, because these are states not magnitudes.

**Two cards beside it:**
- `Families Where Translation Is Required` — 19,569
- `Families Where Translation Is Optional` — 17,206

**A text box** carrying the source line, verbatim, because the whole argument
rests on it:

> Language-Rank-Tiers-2016Updt-Final.xlsx — 2016 Census Update Data
> (Most current as of October 2018). Appendix C, policy INF-14-2-AEO.

### Page 3 — "Who provides what"

**Matrix** (visual type: **Matrix**):
- Rows: `dim_language[language]`
- Columns: `dim_agency[sector]`
- Values: `Best Written Tier`
- Conditional formatting → Background colour → **Gradient**, minimum = pale blue,
  maximum = `#2a78d6`. One hue, light to dark, because tier is a magnitude.

Filter rows to the top 20 languages by families so the matrix stays readable.

**Second visual, stacked bar**: `dim_agency[sector]` on the axis,
`Count of fact_provision` as the value, legend = `fact_provision[pathway_type]`.
This is the one place the three identity colours are used. Assign them in fixed
order: blue = `in_language_document`, orange = `machine_widget`, aqua = `none`.
**Turn data labels on** — the aqua requires it.

### Page 4 — "Where you can walk in"

**Map** (visual type: **Map**, the basic one):
- Latitude: `fact_service_point[lat]`
- Longitude: `fact_service_point[lon]`
- Legend: `fact_service_point[sector]`
- Size: leave empty. Bubble size encoding a count here would imply a magnitude
  that does not exist.

**Slicer: `dim_language[language]`, single select.** This is the page's whole
point. Pick Dari and the map empties out. Pick Spanish and it fills.

**Card:** `Families In Access Deserts`.

**Table below**: `fact_access_desert` filtered to `is_access_desert = True`,
columns district, language, families, sorted descending.

**Text box, mandatory**, because the number is a floor and not the full picture:

> Access deserts are computed from library branches and transit service points
> only. Schools, cities, clinics, food banks and legal aid do not publish
> machine-readable locations and are not represented here.

---

## 6. Publish

1. **File → Save as** → `language-access-skc.pbix` in the repo root.
2. **Home → Publish → My workspace.**
3. In Power BI Service, open the report → **Share** → set link access to
   *people in your organisation* or *anyone with the link*, depending on the
   account.
4. Put the link in the README.

## 7. Before you call it done

- Every page has a title in plain words, not a metric name.
- No chart has two y-axes anywhere.
- Every colour means the same thing on every page.
- Every visual using the aqua has data labels turned on.
- Page 1 carries the measured figure (1,760), the verification count
  (153 of 155), and the text box that connects them. Never the optimistic
  number alone, and never the raw range on a card.
- The access-desert caveat text box is present on page 4.
