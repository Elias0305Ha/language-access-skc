"""
Phase 3, library sector: freeze the three KCLS sources we score from.

Why three separate files instead of one scrape:
  1. locations  -> WHERE the branches are        (feeds the Phase 4 map)
  2. collections -> WHICH languages have books, BY BRANCH   (written supply)
  3. interpreters -> WHICH languages get a human            (oral supply)

They are different claims from different pages, so they get different
files. If KCLS re-publishes one of them next month we can tell which
number moved.

Nothing is parsed here. This script only downloads and freezes.
Parsing lives in parse_kcls.py so a parser bug never costs a re-download.
"""

import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

RAW = Path("data/raw")

# KCLS's own web server rejects non-browser clients with a 403.
# This is not a workaround for a paywall or a login; the pages are public.
# It is only that the CDN filters on User-Agent.
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"

SOURCES = [
    # (filename, url, kind)
    # The public locations list is rendered from this JSON API. limit=100
    # because the default page size is 10 and there are 51 branches. If a
    # future run reports fewer than 51, KCLS changed something: stop and look.
    ("kcls_locations.json",
     "https://gateway.bibliocommons.com/v2/libraries/kcls/locations?limit=100",
     "json"),

    ("kcls_collections_by_language.html",
     "https://kcls.org/collections-by-language-location/",
     "html"),

    ("kcls_interpreters.html",
     "https://kcls.org/interpreters/",
     "html"),
]


def fetch(url):
    req = Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urlopen(req, timeout=60) as resp:
        return resp.read()


def main():
    RAW.mkdir(parents=True, exist_ok=True)

    for name, url, kind in SOURCES:
        dest = RAW / name

        # Freeze rule: never re-download over a file we already have.
        # Delete the file by hand if you deliberately want a fresh capture.
        if dest.exists():
            print(f"skip   {name}  (already on disk, {dest.stat().st_size:,} bytes)")
            continue

        print(f"fetch  {name}")
        try:
            body = fetch(url)
        except (HTTPError, URLError) as e:
            # Print the URL, not just the exception. A bare
            # "HTTP Error 403" tells you nothing about which of three
            # sources failed.
            print(f"  FAILED {url}\n  {type(e).__name__}: {e}", file=sys.stderr)
            continue

        if kind == "json":
            # Validate before writing. A server that answers a bad request
            # with an HTML error page and HTTP 200 would otherwise leave us
            # with a .json file full of HTML that only explodes three
            # scripts later.
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError as e:
                print(f"  NOT JSON from {url}\n  {e}\n  first 300 bytes:\n  {body[:300]!r}",
                      file=sys.stderr)
                continue
            n = len(parsed.get("entities", {}).get("locations", {}))
            print(f"  parsed ok, {n} locations")
            if n < 51:
                print(f"  WARNING: expected at least 51 branches, got {n}", file=sys.stderr)

        dest.write_bytes(body)
        print(f"  wrote {dest}  ({len(body):,} bytes)")

    print("\ncapture date to record on every KCLS inventory row: today's date")


if __name__ == "__main__":
    main()
