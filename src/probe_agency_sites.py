"""
Phase 3: a reusable first-pass profiler for an agency website.

Written once because the remaining sectors are the same job repeated:
eight cities, then legal aid, food assistance and health clinics. Each
needs the same four questions answered before any tier can be assigned.

  1. Does the site run a machine translation widget, and is its language
     list RESTRICTED? A restricted list is a deliberate choice about who
     gets served, and it was one of the sharpest findings in Phase 1.
  2. Does the site publish human-translated pages? Detected from the
     sitemap by language-named slugs and locale path prefixes.
  3. What does robots.txt permit, and does it block translated paths the
     way kingcounty.gov does?
  4. How large is the site? A 40-page city site and a 12,000-page county
     site cannot be compared on raw counts of anything.

This script only PROFILES. It assigns no tiers. Scoring happens in a
per-sector build script, against the frozen output of this one, so a
change to the rule never requires refetching.

Output: data/raw/agency_site_profiles.json
"""

import json
import re
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

OUT = Path("data/raw/agency_site_profiles.json")
OUT_URLS = Path("data/raw/agency_sitemap_urls.json")
ALL_URLS = {}
DELAY_SECONDS = 0.4

# Several municipal sites sit behind a CDN that rejects requests without a
# full browser header set. These are the ordinary headers a browser sends;
# nothing here defeats an access control, it satisfies a bot filter.
# Kent, Renton and SeaTac sit behind Akamai bot management, which serves
# robots.txt to anyone but returns 403 for HTML unless the full modern
# browser header set is present. Sec-Fetch-* and sec-ch-ua are the
# difference between 403 and 200; a partial set is not enough.
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/128.0.0.0 Safari/537.36"),
    "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,"
               "image/avif,image/webp,*/*;q=0.8"),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "identity",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

AGENCIES = [
    # (agency_id, display name, sector, base url)
    ("city_auburn",      "City of Auburn",      "city", "https://www.auburnwa.gov"),
    ("city_burien",      "City of Burien",      "city", "https://www.burienwa.gov"),
    ("city_desmoines",   "City of Des Moines",  "city", "https://www.desmoineswa.gov"),
    ("city_federalway",  "City of Federal Way", "city", "https://www.federalwaywa.gov"),
    ("city_kent",        "City of Kent",        "city", "https://www.kentwa.gov"),
    ("city_renton",      "City of Renton",      "city", "https://www.rentonwa.gov"),
    ("city_seatac",      "City of SeaTac",      "city", "https://www.seatacwa.gov"),
    ("city_tukwila",     "City of Tukwila",     "city", "https://www.tukwilawa.gov"),

    # Legal aid. Unlike cities there is no fixed roster, so the selection
    # is a judgment and is recorded here rather than left implicit.
    # Included: organisations providing free civil legal help to South
    # King County residents, either from an office in the study area or
    # county/state-wide. Excluded: criminal defence (a different right,
    # with its own interpreter mandate), private firms, and referral
    # directories that provide no service themselves.
    ("legal_nwjustice",  "Northwest Justice Project", "legal", "https://nwjustice.org"),
    # The statewide legal self-help library, run by NJP. Matters
    # disproportionately: if free translated legal materials already exist
    # here, then a local provider offering none is the same shape of
    # finding as the OSPI multilingual templates in the schools sector.
    ("legal_walawhelp",  "WashingtonLawHelp",         "legal", "https://www.washingtonlawhelp.org"),
    ("legal_kcba",       "King County Bar Association", "legal", "https://www.kcba.org"),
    ("legal_elap",       "Eastside Legal Assistance Program", "legal", "https://elap.org"),
    ("legal_nwirp",      "NW Immigrant Rights Project", "legal", "https://www.nwirp.org"),
    ("legal_solidground", "Solid Ground",             "legal", "https://www.solid-ground.org"),
    ("legal_colectiva",  "Colectiva Legal del Pueblo", "legal", "https://colectivalegal.org"),
    ("legal_teamchild",  "TeamChild",                 "legal", "https://www.teamchild.org"),
    ("legal_entrehermanos", "Entre Hermanos",         "legal", "https://entrehermanos.org"),
    # Catholic Community Services (Tenant Law Center) returns 403 to every
    # header set tried. Recorded as unreachable rather than as an agency
    # with no translation, which is a different claim entirely.
    ("legal_ccsww",      "Catholic Community Services of Western Washington",
     "legal", "https://ccsww.org"),

    # Food assistance. Selection: food banks physically serving the six
    # study districts, plus the two regional distributors that supply them
    # and the two state channels people must go through to get SNAP.
    # The state channels matter most: a food bank hands you groceries in
    # any language, but a benefits APPLICATION is a consequential document
    # in the same sense as a school placement letter.
    ("food_auburn",      "The Auburn Food Bank",  "food", "https://www.theauburnfoodbank.org"),
    ("food_kent",        "Kent Food Bank and Emergency Services", "food", "https://kentfoodbank.org"),
    ("food_desmoines",   "Des Moines Area Food Bank", "food", "https://myfoodbank.org"),
    ("food_msc",         "Multi-Service Center (Federal Way)", "food", "https://mschelps.org"),
    ("food_highline",    "Highline Area Food Bank", "food", "https://highlineareafoodbank.org"),
    ("food_whitecenter", "White Center Food Bank", "food", "https://www.whitecenterfoodbank.org"),
    ("food_tukwila",     "Tukwila Pantry",        "food", "https://www.tukwilapantry.org"),
    ("food_renton_sa",   "Salvation Army Renton", "food", "https://renton.salvationarmy.org"),
    ("food_nwharvest",   "Northwest Harvest",     "food", "https://www.northwestharvest.org"),
    ("food_foodlifeline", "Food Lifeline",        "food", "https://foodlifeline.org"),
    ("food_dshs",        "DSHS Basic Food (SNAP)", "food", "https://www.dshs.wa.gov"),
    ("food_waconnection", "Washington Connection (benefits application)",
     "food", "https://www.washingtonconnection.org"),

    # Health. Selection: the safety-net providers a low-income,
    # limited-English resident of the study area actually uses, plus the
    # two state channels that gate coverage. Excluded: private insurers
    # and specialty practices, which serve a different population.
    #
    # Public Health Seattle and King County is handled in the builder
    # rather than here: it lives under kingcounty.gov, whose sitemap is
    # already frozen, and probing it separately would report 11,587 pages
    # for a single department.
    ("health_healthpoint", "HealthPoint", "health", "https://healthpointchc.org"),
    ("health_seamar",      "Sea Mar Community Health Centers", "health", "https://www.seamar.org"),
    ("health_ichs",        "International Community Health Services", "health", "https://www.ichs.com"),
    ("health_neighborcare", "Neighborcare Health", "health", "https://neighborcare.org"),
    ("health_globaltolocal", "Global to Local", "health", "https://globaltolocal.org"),
    ("health_valleymed",   "Valley Medical Center", "health", "https://valleymed.org"),
    ("health_multicare",   "MultiCare Health System", "health", "https://www.multicare.org"),
    ("health_vmfh",        "Virginia Mason Franciscan Health", "health", "https://www.vmfh.org"),
    # State channels. Apple Health (Medicaid) eligibility and the
    # insurance marketplace application are the consequential documents
    # in this sector, the analogue of SNAP form 14-001.
    ("health_hca",         "WA Health Care Authority (Apple Health)", "health", "https://www.hca.wa.gov"),
    ("health_planfinder",  "Washington Healthplanfinder", "health", "https://www.wahealthplanfinder.org"),
    ("health_doh",         "WA Department of Health", "health", "https://doh.wa.gov"),
]

# Language-named slugs, the pattern that found 247 translated pages on
# kingcounty.gov. Deliberately a closed list: matching any two-letter
# ending turned 'movies-and-tv-es' into a language and lost a real page.
LANGUAGE_SLUGS = [
    "amharic", "arabic", "burmese", "cambodian", "chinese", "chuukese", "dari",
    "farsi", "french", "hindi", "hmong", "ilocano", "japanese", "karen", "khmer",
    "korean", "lao", "marshallese", "mien", "nepali", "oromo", "pashto",
    "persian", "portuguese", "punjabi", "romanian", "russian", "samoan",
    "somali", "spanish", "swahili", "tagalog", "thai", "tigrinya", "tongan",
    "turkish", "ukrainian", "urdu", "vietnamese",
]

WIDGET_PATTERNS = {
    "google_translate": r"translate\.google|goog-te|googleTranslateElement",
    "gtranslate": r"gtranslate|GTranslate",
    "weglot": r"weglot",
    "localize": r"localizejs|localize\.js",
    "transifex": r"transifex",
    # OpenCities builds its own switcher on a query parameter and loads no
    # vendor script. Renton looked like it had no translation at all until
    # this was added; it actually offers a curated 17-language list.
    "opencities_oc_lang": r"oc_lang=",
}

# How each mechanism declares its language list. A RESTRICTED list is the
# finding, because it is a deliberate choice about who gets served.
RESTRICTION_PATTERNS = [
    # Google Translate widget, narrowed
    (r"""includedLanguages\s*:\s*['"]([^'"]+)['"]""",
     lambda m: m.group(1).split(",")),
    # GTranslate plugin config
    (r'"languages"\s*:\s*\[([^\]]+)\]', lambda m: re.findall(r'"([a-z\-]{2,7})"', m.group(1))),
]


def get(url, timeout=45):
    try:
        with urlopen(Request(url, headers=HEADERS), timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace"), r.url
    except HTTPError as e:
        return e.code, "", url
    except (URLError, TimeoutError) as e:
        return type(e).__name__, "", url
    except Exception as e:
        return type(e).__name__, "", url


def find_widget(body):
    found = [name for name, pat in WIDGET_PATTERNS.items()
             if re.search(pat, body, re.I)]
    restricted = None
    # An ABSENT restriction means the widget is unrestricted, which is a
    # different finding from a short explicit list. Both are recorded.
    for pat, extract in RESTRICTION_PATTERNS:
        m = re.search(pat, body)
        if m:
            got = [x.strip() for x in extract(m) if x and x.strip()]
            if got:                      # an empty match is not a restriction
                restricted = got
                break

    # OpenCities enumerates its languages as links rather than as a config
    # blob, so it needs its own reader. Renton looked like it had no
    # translation at all until this was added; it actually publishes a
    # curated 17-language list.
    if not restricted and "opencities_oc_lang" in found:
        codes = sorted({c for c in re.findall(r"oc_lang=([A-Za-z\-]+)", body)
                        if c.lower() not in ("en-us", "en")})
        if codes:
            restricted = codes
    return found, restricted


def collect_sitemap_urls(base, depth=0, seen=None):
    """Follow a sitemap index one level down. Returns page URLs."""
    seen = seen if seen is not None else set()
    status, body, _ = get(base)
    if not body:
        return [], status
    locs = re.findall(r"<loc>(.*?)</loc>", body)
    urls, children = [], []
    for l in locs:
        (children if l.lower().endswith(".xml") else urls).append(l)
    if depth == 0:
        for c in children[:40]:          # cap: a few sites index hundreds
            if c in seen:
                continue
            seen.add(c)
            time.sleep(DELAY_SECONDS)
            sub, _ = collect_sitemap_urls(c, depth + 1, seen)
            urls += sub
    return urls, status


def profile(agency_id, name, sector, base):
    print(f"\n=== {name}  {base}")
    rec = {"agency_id": agency_id, "agency_name": name, "sector": sector,
           "base_url": base, "capture_date": date.today().isoformat()}

    status, body, final = get(base)
    rec["home_status"] = status
    rec["final_url"] = final
    if final.rstrip("/") != base.rstrip("/"):
        rec["redirects_to"] = final
        print(f"    redirects to {final}")
    print(f"    home HTTP {status}, {len(body)} bytes")
    if not body:
        rec["error"] = "homepage not retrievable"
        return rec

    widgets, restricted = find_widget(body)
    rec["widgets"] = widgets
    rec["widget_restricted_to"] = restricted
    print(f"    widgets: {widgets or 'none'}")
    if restricted:
        print(f"    RESTRICTED to {len(restricted)}: {restricted}")
    elif widgets:
        print("    unrestricted (no includedLanguages parameter)")

    time.sleep(DELAY_SECONDS)
    rstatus, rbody, _ = get(base.rstrip("/") + "/robots.txt")
    rec["robots_status"] = rstatus
    rec["robots_disallow"] = re.findall(r"(?im)^\s*Disallow:\s*(\S+)", rbody)[:60]
    rec["robots_sitemaps"] = re.findall(r"(?im)^\s*Sitemap:\s*(\S+)", rbody)
    rec["robots_blocks_ai_crawlers"] = bool(
        re.search(r"(?i)User-agent:\s*(ClaudeBot|GPTBot|Google-Extended|CCBot)", rbody))
    print(f"    robots HTTP {rstatus}, {len(rec['robots_disallow'])} disallow rules, "
          f"AI-crawler blocks: {rec['robots_blocks_ai_crawlers']}")

    # Des Moines declares its sitemap as a relative path ("/sitemap.xml").
    # Passing that straight to the fetcher raises ValueError, which this
    # script previously recorded as "0 pages" — an error rendered as an
    # absence of translated content, which is the exact failure this
    # project keeps guarding against.
    candidates = [urljoin(base, sm) for sm in rec["robots_sitemaps"]]         or [base.rstrip("/") + "/sitemap.xml"]
    urls, sstatus = [], None
    for sm in candidates[:3]:
        time.sleep(DELAY_SECONDS)
        u, sstatus = collect_sitemap_urls(sm)
        urls += u
    urls = sorted(set(urls))
    rec["sitemap_status"] = sstatus
    rec["sitemap_page_count"] = len(urls)
    print(f"    sitemap: {len(urls)} pages (HTTP {sstatus})")

    hits = {}
    for u in urls:
        slug = u.rstrip("/").split("/")[-1].lower()
        for L in LANGUAGE_SLUGS:
            if slug == L or slug.endswith("-" + L) or slug.endswith("_" + L):
                hits.setdefault(L, []).append(u)
                break
    rec["language_named_pages"] = {k: v[:10] for k, v in hits.items()}
    rec["language_named_page_count"] = sum(len(v) for v in hits.values())
    print(f"    language-named pages: {rec['language_named_page_count']} "
          f"across {len(hits)} languages {sorted(hits)}")

    locales = sorted({m.group(1) for u in urls
                      if (m := re.match(r"https?://[^/]+/([a-z]{2}(?:-[A-Za-z]{2})?)(?:/|$)", u))
                      and m.group(1) != "en"})
    rec["locale_prefixes_in_sitemap"] = locales[:20]

    # Pages about language access itself. These are where an oral tier
    # would be evidenced: an interpreter offer, a translation policy, a
    # Title VI notice. Absence here is as informative as presence.
    ACCESS_PAT = re.compile(
        r"(language-access|languageaccess|interpret|translat|title-vi|titlevi"
        r"|limited-english|lep\b|multilingual)", re.I)
    access = [u for u in urls if ACCESS_PAT.search(u)]
    rec["language_access_pages"] = access[:25]
    rec["language_access_page_count"] = len(access)
    print(f"    language-access pages: {len(access)}")
    for a in access[:5]:
        print(f"       {a}")

    # Keep every URL. Later sectors and the Phase 4 evidence archive both
    # need them, and refetching a sitemap to answer a new question is
    # wasted traffic against someone else's server.
    ALL_URLS.setdefault(agency_id, urls)
    return rec


def main():
    # Incremental by design. Each new sector adds rows to AGENCIES; an
    # all-or-nothing skip would mean refetching every previously profiled
    # site to add one, which is wasted traffic against other people's
    # servers. Delete an agency's entry from the JSON to re-profile it.
    out = []
    done = set()
    if OUT.exists():
        out = json.loads(OUT.read_text(encoding="utf-8"))
        done = {r["agency_id"] for r in out}
        print(f"already profiled: {len(done)}")
    if OUT_URLS.exists():
        ALL_URLS.update(json.loads(OUT_URLS.read_text(encoding="utf-8")))

    todo = [a for a in AGENCIES if a[0] not in done]
    print(f"to profile now: {len(todo)}")
    for a in todo:
        try:
            out.append(profile(*a))
        except Exception as e:
            print(f"    UNHANDLED {type(e).__name__}: {e}", file=sys.stderr)
            out.append({"agency_id": a[0], "agency_name": a[1], "sector": a[2],
                        "base_url": a[3], "error": f"{type(e).__name__}: {e}"})
        time.sleep(DELAY_SECONDS)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT}  ({len(out)} agencies)")

    # Keep every sitemap URL. Later sectors, the Phase 4 evidence archive
    # and any re-detection all need them, and refetching a sitemap to
    # answer a new question is wasted traffic against someone else's
    # server.
    OUT_URLS.write_text(json.dumps(ALL_URLS, ensure_ascii=False, indent=0),
                        encoding="utf-8")
    print(f"wrote {OUT_URLS}  ({sum(len(v) for v in ALL_URLS.values())} URLs "
          f"across {len(ALL_URLS)} agencies)")

    print("\nsummary")
    print(f"{'agency':22}{'pages':>7}{'widget':>18}{'restricted':>12}{'lang pages':>12}")
    for r in out:
        print(f"{r['agency_name'][:21]:22}"
              f"{r.get('sitemap_page_count', 0):7}"
              f"{','.join(r.get('widgets') or ['none'])[:17]:>18}"
              f"{(len(r['widget_restricted_to']) if r.get('widget_restricted_to') else '-'):>12}"
              f"{r.get('language_named_page_count', 0):>12}")


if __name__ == "__main__":
    main()
