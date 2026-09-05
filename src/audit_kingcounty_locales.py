"""
Phase 3: test whether King County's seven translated locale paths carry
translated content, or only translated page titles.

Background. kingcounty.gov serves seven locale prefixes:
    /es-ES  /ko-KR  /ru-RU  /so-SO  /uk-UA  /vi-VN  /zh-CN
All seven are blocked in robots.txt, absent from the sitemap, and
unlinked from department pages. All seven return HTTP 200.

The question this script answers is narrow and falsifiable:

    For a sample of real pages, is the body text under a locale prefix
    DIFFERENT from the body text of the same page under /en/?

If the two are identical, the locale path is a routing shell: it serves
English content under a translated title. If they differ, real
translation exists and has to be inventoried language by language.

Method. Sample paths from the frozen English sitemap at a fixed stride
so the sample is reproducible without storing a seed. Fetch each path
under /en/ and under every locale. Normalise the main body text and
compare. Identical text is the null result; the measurement is the
proportion of sampled pages that differ.

Comparing to the English version, rather than running language
detection, avoids the whole class of errors where a detector calls a
page 'Spanish' because it contains the word 'Seattle'.

Output: data/raw/kingcounty_locale_audit.csv
"""

import csv
import html
import json
import re
import sys
import time
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

SITEMAP_URLS = Path("data/raw/kingcounty_sitemap_urls.json")
OUT = Path("data/raw/kingcounty_locale_audit.csv")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"
DELAY_SECONDS = 0.3

LOCALES = ["es-ES", "ko-KR", "ru-RU", "so-SO", "uk-UA", "vi-VN", "zh-CN"]

# Sample size. Small on purpose: this is a one-time capture against a
# public agency's site, and 12 pages across 7 locales is already 96
# requests. A larger sample would not change a result this stark.
SAMPLE_SIZE = 12


def fetch(url):
    try:
        with urlopen(Request(url, headers={"User-Agent": UA}), timeout=60) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except HTTPError as e:
        return e.code, ""
    except URLError as e:
        return type(e).__name__, ""


def body_text(raw_html):
    """Main-content text, normalised, for comparison only.

    Chrome and navigation are stripped because they are identical on
    every page and would dilute any real difference.
    """
    b = re.sub(r"<(script|style|nav|footer|header)[^>]*>.*?</\1>", "",
               raw_html, flags=re.S)
    m = re.search(r"<main.*?</main>", b, re.S)
    if m:
        b = m.group(0)
    t = html.unescape(re.sub(r"<[^>]+>", " ", b))
    return re.sub(r"\s+", " ", t).strip()


def page_title(raw_html):
    m = re.search(r"<title[^>]*>(.*?)</title>", raw_html, re.S)
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""


def main():
    if OUT.exists():
        print(f"skip  {OUT}  (already on disk)")
        return
    if not SITEMAP_URLS.exists():
        sys.exit("run src/fetch_kingcounty_sitemap.py first")

    urls = json.loads(SITEMAP_URLS.read_text(encoding="utf-8"))
    en_paths = [u.split("kingcounty.gov/en", 1)[1]
                for u in urls if "kingcounty.gov/en" in u]

    # Fixed stride, not a random seed: the sample is reproducible from
    # the frozen sitemap alone, with nothing else to record.
    stride = max(len(en_paths) // SAMPLE_SIZE, 1)
    sample = en_paths[::stride][:SAMPLE_SIZE]
    print(f"English pages in sitemap: {len(en_paths)}")
    print(f"sampling every {stride}th, n={len(sample)}\n")

    today = date.today().isoformat()
    rows = []
    for path in sample:
        en_status, en_html = fetch("https://kingcounty.gov/en" + path)
        en_body = body_text(en_html) if en_html else ""
        time.sleep(DELAY_SECONDS)

        print(f"{path[:58]:60} en={en_status} chars={len(en_body)}")
        for loc in LOCALES:
            st, raw = fetch(f"https://kingcounty.gov/{loc}{path}")
            body = body_text(raw) if raw else ""
            same = (body == en_body) if (body and en_body) else None
            rows.append({
                "path": path,
                "locale": loc,
                "en_status": en_status,
                "locale_status": st,
                "en_body_chars": len(en_body),
                "locale_body_chars": len(body),
                "body_identical_to_english": "" if same is None else same,
                "locale_title": page_title(raw) if raw else "",
                "capture_date": today,
            })
            flag = "SAME" if same else ("differs" if same is False else "?")
            print(f"    {loc}  http={st:<4} chars={len(body):<6} {flag}")
            time.sleep(DELAY_SECONDS)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {OUT}  ({len(rows)} rows)")

    comparable = [r for r in rows if r["body_identical_to_english"] != ""]
    identical = [r for r in comparable if r["body_identical_to_english"] is True]
    print(f"\ncomparable page/locale pairs: {len(comparable)}")
    print(f"body identical to English:    {len(identical)}")
    if comparable:
        pct = 100.0 * len(identical) / len(comparable)
        print(f"                              {pct:.1f}%")


if __name__ == "__main__":
    main()
