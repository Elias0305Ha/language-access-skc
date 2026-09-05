"""
Phase 3: freeze King County's own sitemap.

Two uses:
  1. It is the page list the locale audit samples from.
  2. It is itself evidence. The sitemap declares which pages King County
     wants indexed. Every entry is under /en/. None of the seven
     translated locale paths appear, which is one of the three
     independent mechanisms keeping that content out of search results.
     The other two are the robots.txt Disallow rules and the absence of
     any link from department pages.

Output: data/raw/kingcounty_sitemap_urls.json
"""

import json
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

OUT = Path("data/raw/kingcounty_sitemap_urls.json")
# Declared in https://kingcounty.gov/robots.txt
URL = "https://kingcounty.gov/-/media/SitemapXml"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"

LOCALES = ["es-ES", "ko-KR", "ru-RU", "so-SO", "uk-UA", "vi-VN", "zh-CN"]


def main():
    if OUT.exists():
        urls = json.loads(OUT.read_text(encoding="utf-8"))
        print(f"skip  {OUT}  (already on disk, {len(urls)} URLs)")
        return

    try:
        with urlopen(Request(URL, headers={"User-Agent": UA}), timeout=120) as r:
            body = r.read().decode("utf-8", "replace")
    except (HTTPError, URLError) as e:
        print(f"FAILED {URL}\n  {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)

    urls = re.findall(r"<loc>(.*?)</loc>", body)
    print(f"sitemap entries: {len(urls)}")

    # The finding, measured rather than assumed.
    en = sum(1 for u in urls if "kingcounty.gov/en" in u)
    print(f"under /en/: {en}")
    for loc in LOCALES:
        n = sum(1 for u in urls if f"kingcounty.gov/{loc}" in u)
        print(f"under /{loc}/: {n}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(sorted(set(urls)), indent=0), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
