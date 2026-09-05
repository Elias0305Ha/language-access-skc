"""
Phase 3: freeze the list of languages the Google Translate website widget
supports.

Why this belongs in the project. The classification rule says a machine
translation widget can satisfy the request-pathway test for discovery,
which makes an agency's widget worth tier 2 in every language the widget
covers. So "which languages does the widget cover" is a scoring input,
not trivia, and it must come from a source rather than from memory.

An unrestricted widget therefore hands out tier 2 broadly, which is
exactly why the gap index weights the 2-to-3 step more heavily than
0-to-2. Tier 2 does not discriminate between agencies. Tier 3 does.

Source: the endpoint the widget itself calls to populate its language
menu.

Output: data/raw/google_translate_languages.json  {code: English name}
"""

import json
import sys
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

OUT = Path("data/raw/google_translate_languages.json")
URL = "https://translate.googleapis.com/translate_a/l?client=wt&hl=en"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"


def main():
    if OUT.exists():
        d = json.loads(OUT.read_text(encoding="utf-8"))
        print(f"skip  {OUT}  (already on disk, {len(d['languages'])} languages)")
        return

    try:
        with urlopen(Request(URL, headers={"User-Agent": UA}), timeout=60) as r:
            payload = json.loads(r.read().decode("utf-8"))
    except (HTTPError, URLError) as e:
        print(f"FAILED {URL}\n  {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"NOT JSON from {URL}\n  {e}", file=sys.stderr)
        sys.exit(1)

    langs = payload.get("tl") or {}
    if not langs:
        sys.exit(f"no target languages in response; keys were {list(payload)}")

    # encoding='utf-8' is not optional here. Language names contain
    # characters outside the Windows default codepage, and writing
    # without it produces a file that cannot be read back.
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"captured": date.today().isoformat(),
                    "source": URL,
                    "languages": langs},
                   ensure_ascii=False, indent=1),
        encoding="utf-8")

    print(f"wrote {OUT}  ({len(langs)} languages)")


if __name__ == "__main__":
    main()
