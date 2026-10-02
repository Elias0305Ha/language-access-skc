# Project brief: Language Access in South King County

For my resume agent. Everything here is real and checkable in the repo.

**Repo:** https://github.com/Elias0305Ha/language-access-skc
**Me:** Elias Hakenso, worked alone, about three weeks, 32 commits.

---

## What it is

I measured the gap between the languages people speak at home in South King
County and the languages public agencies there actually serve.

Then I built a dashboard from it and sent a memo to the county office that can
fix it.

## How it works

1. Count who speaks what, where. (demand)
2. Check what each agency actually provides. (supply)
3. Subtract. Rank. Map.

## Size of it

- 6 school districts, 36,775 families, 140 languages
- 51 agencies across 7 sectors: food, health, legal, city, schools, transit, library
- 6,272 agency-by-language rows scored, each with an evidence link and a date
- 95 physical locations mapped
- About 30 Python scripts
- 4-page Power BI report on an 8-table model, 23 DAX measures

## Tools

Python (pandas, requests, BeautifulSoup, GeoPandas), Census API, Socrata API,
Power BI Desktop, DAX, star schema modelling, Git, TIGER shapefiles, GTFS
transit feeds.

## What I found

King County has a law saying which languages must get translated documents.
It points to a ranked list of languages. That list was built on 2016 data and
has never been updated.

**Dari is the second biggest home language here, 3,040 families, and it is not
on that list at all.** Neither is Pashto (1,127) or Marshallese (446).

Other findings:

- 53% of families speak the one language where translation is required.
  The other 47% speak a language where it is optional or unmentioned.
- 393 families get nothing in writing from any agency in any sector.
- King County has 7 translated website paths. In my sample, 71 of 77 pages
  were the English page.
- Of 95 physical service points, Spanish is served at 44. Dari at 2. Pashto,
  Tigrinya and Khmer at zero.

## The three things that make it good

**1. I tested a standard method and threw it out.**
The usual way to estimate a language in a small area is to take its share of a
broad group measured somewhere bigger, and apply that share. I tested it. The
error was 7.1 percentage points across 219 rows. It predicted Auburn was 7.5%
Marshallese. It is 63.1%. So I rejected the method and made a less pretty map
that is actually true.

**2. I wrote the scoring rule before I collected any data.**
That way the rule could not be bent to fit the answer.

**3. I published the uncertainty instead of hiding it.**
155 rows claim a translated document exists. Only 2 have been read by someone
who reads the language, and 2 of the 4 checked turned out to be machine
translation. So every number is published twice, best case and worst case.

## Robustness

I ran 11 different weighting scenarios. The main number moved only between 376
and 393. One scenario flipped the ranking and I reported it instead of hiding
it.

## What I shipped

- Public GitHub repo with all code and frozen source data
- 4-page Power BI report, published, with the file in the repo
- A methodology writeup, a data dictionary, and the classification rule
- A one-page memo, sent to the King County Language Access Program

---

## Resume bullets to pick from

- Measured language-access gaps across 51 public agencies and 7 sectors,
  scoring 6,272 agency-language pairs against a rule written before data
  collection began.
- Found that King County's legally binding language list, built on 2016 data,
  omits the region's second most common home language (3,040 families).
  Delivered it as a memo to the office with authority to act.
- Tested and rejected a standard estimation method after validation showed
  7.1 percentage-point error, avoiding a plausible but fabricated map.
  Published the negative result.
- Built an 8-table Power BI star schema with 23 DAX measures and a 4-page
  published report.
- Ran an 11-scenario sensitivity analysis and reported the one scenario that
  reversed the ranking.
- Combined Census ACS tables and PUMS microdata with state education data
  across tract, PUMA and school-district geographies.

---

## Interview answers

**A time you were wrong:** My first gap index scored a fully served
district-language pair higher than one with nothing at all. I had used one
scale for two different kinds of access. I split them and reported three
numbers instead of one.

**A time you pushed back:** I was advised to cut the inventory from seven
sectors to three to save time. I refused. The comparison across sectors turned
out to be a finding in itself, and page three of the dashboard only exists
because of that call.

**What you would do differently:** Add a second person to score a sample
independently. Every judgment in the project is mine and there is no
reliability statistic. It would be cheap and it is the biggest hole left.

**Why this project:** I live in the study area and speak Amharic. The only two
translation claims anyone verified in the whole dataset are Amharic, because I
was the only person who could read the document. That is a real limitation and
I wrote it into the repo rather than leaving it out.
