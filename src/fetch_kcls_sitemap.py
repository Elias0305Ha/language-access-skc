"""
Phase 3: freeze the full list of kcls.org page URLs.

Why: written_tier asks whether the agency has published anything in a
language. Clicking around cannot prove absence. The sitemap can, because
it is the site's own declaration of what pages exist.

Translated pages on kcls.org are separate URLs with a language suffix,
e.g. library-cards-es, interpreters-am. So counting suffixed slugs gives
a defensible count of human-translated pages per language, and, more
importantly, a defensible ZERO for languages that have none.

Limitation to state in the writeup: the sitemap lists pages, not files.
A translated PDF sitting in the media library would not appear here.

Output: data/raw/kcls_page_urls.json
"""

import json
import re
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

OUT = Path("data/raw/kcls_page_urls.json")
INDEX = "https://kcls.org/sitemap.xml"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"

# Be a polite guest. See the web-collection policy in docs/METHODOLOGY.md.
DELAY_SECONDS = 0.3


def get(url):
    with urlopen(Request(url, headers={"User-Agent": UA}), timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def main():
    if OUT.exists():
        urls = json.loads(OUT.read_text(encoding="utf-8"))
        print(f"skip  {OUT}  (already on disk, {len(urls)} URLs)")
        return

    try:
        index = get(INDEX)
    except (HTTPError, URLError) as e:
        print(f"FAILED {INDEX}\n  {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)

    # The index points at ~134 child sitemaps. Only the 'page' ones hold
    # standing service pages; 'post' ones are blog entries and events,
    # which are not agency communications in the tier-3 sense.
    subs = [u for u in re.findall(r"<loc>(.*?)</loc>", index) if "pt-page" in u]
    print(f"child sitemaps of type 'page': {len(subs)}")

    urls = []
    for s in subs:
        urls += re.findall(r"<loc>(.*?)</loc>", get(s))
        time.sleep(DELAY_SECONDS)

    urls = sorted(set(urls))
    print(f"distinct page URLs: {len(urls)}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(urls, indent=0), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
