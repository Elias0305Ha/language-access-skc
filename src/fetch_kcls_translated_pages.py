"""
Phase 3: identify and freeze KCLS's translated pages, with evidence.

Method: kcls.org publishes translations as separate URLs with a language
suffix (library-cards-es, interpreters-am). Detect those in the frozen
sitemap, then fetch each one and record its <h1>.

Why record the h1 rather than just count URLs:
  A suffix is not proof of a translation. 'best-books-es' is titled
  "Best Books (Spanish)", an English page listing Spanish books.
  'library-cards-es' is titled "Obtenga una tarjeta de biblioteca", a
  genuine Spanish page. Counting URLs alone would score those the same.

  So the output carries a per-page heading, and the inventory reports
  both a raw count and a heading-verified count. The gap between them is
  a real measurement, not noise to be hidden.

Output: data/raw/kcls_translated_pages.csv
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

URLS = Path("data/raw/kcls_page_urls.json")
OUT = Path("data/raw/kcls_translated_pages.csv")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"
DELAY_SECONDS = 0.25

# Only suffixes KCLS actually uses. Deliberately not every ISO code:
# a permissive list turns any slug ending in two letters into a false
# positive. Unrecognised suffixes are printed so the list can grow on
# evidence rather than on speculation.
SUFFIX_TO_LANGUAGE = {
    "es": "Spanish", "am": "Amharic", "so": "Somali", "ar": "Arabic",
    "ru": "Russian", "uk": "Ukrainian", "vi": "Vietnamese",
    "pa": "Pashto",        # KCLS's own slug; the page content is Pashto, not Punjabi
    "zh-ch": "Chinese",    # KCLS uses both spellings for Chinese
    "zh-cn": "Chinese",
}

# Reporting only. Matching on this pattern to DETECT languages was a bug:
# it read 'movies-and-tv-es' as the two-part code 'tv-es' and discarded a
# real Spanish page. Detection now tests known suffixes directly, longest
# first, so a two-part code can never shadow a one-part one.
SUFFIX_RE = re.compile(r"-([a-z]{2}(?:-[a-z]{2})?)$")


def detect_language(slug):
    for suf in sorted(SUFFIX_TO_LANGUAGE, key=len, reverse=True):
        if slug.endswith("-" + suf):
            return SUFFIX_TO_LANGUAGE[suf]
    return None

# Latin script alone cannot tell Spanish from English, so this flag only
# proves a NON-Latin heading. Spanish and Somali are judged by eye from
# the recorded h1, which is why the h1 is stored rather than a verdict.
def non_latin(s):
    return any(ord(c) > 0x250 for c in s)


def main():
    if OUT.exists():
        print(f"skip  {OUT}  (already on disk)")
        return
    if not URLS.exists():
        sys.exit("run src/fetch_kcls_sitemap.py first")

    urls = json.loads(URLS.read_text(encoding="utf-8"))
    candidates, unknown = [], set()
    for u in urls:
        slug = u.rstrip("/").split("/")[-1]
        lang = detect_language(slug)
        if lang:
            candidates.append((lang, slug, u))
            continue
        m = SUFFIX_RE.search(slug)
        if m:
            unknown.add(m.group(1))

    print(f"pages in sitemap: {len(urls)}")
    print(f"language-suffixed candidates: {len(candidates)}")
    if unknown:
        print(f"two-letter endings NOT treated as languages: {sorted(unknown)}")

    today = date.today().isoformat()
    rows = []
    for lang, slug, u in candidates:
        try:
            with urlopen(Request(u, headers={"User-Agent": UA}), timeout=45) as r:
                body = r.read().decode("utf-8", "replace")
                status = r.status
        except (HTTPError, URLError) as e:
            print(f"  FAILED {u}  {type(e).__name__}: {e}", file=sys.stderr)
            rows.append({"language": lang, "slug": slug, "url": u, "http_status": "",
                         "h1": "", "h1_non_latin": "", "capture_date": today})
            continue

        m = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
        h1 = html.unescape(re.sub("<[^>]+>", "", m.group(1))).strip() if m else ""
        rows.append({"language": lang, "slug": slug, "url": u, "http_status": status,
                     "h1": h1, "h1_non_latin": non_latin(h1), "capture_date": today})
        time.sleep(DELAY_SECONDS)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(rows)

    print(f"wrote {OUT}  ({len(rows)} rows)")
    from collections import Counter
    for lang, n in Counter(r["language"] for r in rows).most_common():
        print(f"  {lang:11} {n}")


if __name__ == "__main__":
    main()
