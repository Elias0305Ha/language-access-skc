# Prompt for a new Claude Code session

Copy everything inside the box and paste it as your first message.

---

```
Read CLAUDE.md first, then docs/MEMO.md and powerbi/BUILD_GUIDE.md. Do not
re-run any fetch_*.py script: all source data is frozen in data/raw/ on
purpose and re-downloading would break reproducibility.

WHERE THE PROJECT IS

Phases 1 to 4 are complete: demand, census validation, a 7-sector supply
inventory covering 51 agencies and 6,272 scored rows, the gap index, the
access-desert map layers, the sensitivity analysis, and the King County
tier-map exhibit. Phase 5's memo is written and finished at docs/MEMO.md.

The only thing left is the Power BI dashboard, then a README and putting
the repo on GitHub. There is no git remote yet.

WHERE I AM STUCK

language-access-skc.pbix exists in the repo root. I have already:
  - loaded all 8 tables from powerbi/
  - connected the relationships (8 boxes, all joined, confirmed in Model view)

The report itself is still empty: one blank page, zero visuals.

The immediate open question is whether the DAX measures from
powerbi/measures.dax have been added yet. In Report view, under fact_gap in
the Fields panel, I need to check whether anything shows a calculator icon
with names like "Families in Selection" or "Gap Score (Optimistic)".

WHAT I NEED FROM YOU

Walk me through building the four report pages described in
powerbi/BUILD_GUIDE.md section 5. I am new to Power BI and I do not
remember the interface, so be specific about where to click.

HOW I WORK

- Give me ONE step at a time and wait for me to do it. Never a list of steps.
- I run everything myself. Write scripts into src/ and show me the code;
  do not run them for me unless I ask.
- Explain why, not just what, especially where a naive version would be
  silently wrong.
- Be direct. Bullets over paragraphs. No em dashes.
- Challenge me if I am about to do something indefensible.
- Check before asserting. Verify against the actual files rather than
  stating things from memory. This has caught real errors in this project
  several times.
- I can paste screenshots in this app, so ask for one whenever it is faster
  than describing a screen.

ONE THING TO KNOW ABOUT THE DATA

155 rows in the dataset claim a human-translated document. Only 2 have been
verified by someone who reads the language, and of the 4 that were checked,
2 turned out to be machine translation. Every headline number must carry
that caveat. The build guide's Page 1 spec handles it; do not simplify it
away.
```

---

## After pasting

In the desktop app, open the folder `C:\projects\language-access-skc` as the
project. If you want the earlier conversation instead of a fresh start, use
`/resume` and pick the session from the list. The prompt above works either
way.
