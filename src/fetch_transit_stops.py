"""
Phase 4: freeze the transit GTFS feeds and extract service points.

Why not every bus stop. King County Metro's feed carries roughly eight
thousand stops. A bus stop is a pole and a sign; it provides no service
in any language, has no staff, no ticket machine and no printed
information. Mapping all of them would put dense point clutter over the
study area and would misrepresent what "a place you can get help" means.

What counts as a service point here:
  - GTFS location_type == 1, a station in the feed's own terms
  - or a stop whose name marks it as a transit centre, park and ride, or
    light rail station

Those are the places with signage, ticket vending machines, wayfinding
and sometimes staff, which is where language access is either present or
absent in a way a rider experiences.

Sources:
  King County Metro   https://metro.kingcounty.gov/GTFS/google_transit.zip
  Sound Transit       https://gtfs.sound.obaweb.org/prod/40_gtfs.zip

Output: data/raw/gtfs_kcmetro.zip, data/raw/gtfs_soundtransit.zip
        data/processed/transit_service_points.csv
"""

import csv
import io
import re
import sys
import zipfile
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import pandas as pd

RAW = Path("data/raw")
OUT = Path("data/processed/transit_service_points.csv")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0"}

FEEDS = [
    ("kcmetro", "King County Metro", "gtfs_kcmetro.zip",
     "https://metro.kingcounty.gov/GTFS/google_transit.zip"),
    ("sound_transit", "Sound Transit", "gtfs_soundtransit.zip",
     "https://gtfs.sound.obaweb.org/prod/40_gtfs.zip"),
]

# Name patterns that mark a real service point rather than a pole.
SERVICE_POINT_RE = re.compile(
    r"(transit cent(er|re)|park\s*&\s*ride|park and ride|\bstation\b|"
    r"\bLink\b|transit hub)", re.I)


def fetch(name, url):
    dest = RAW / name
    if dest.exists():
        print(f"skip  {name}  (already on disk, {dest.stat().st_size:,} bytes)")
        return dest
    print(f"fetch {url}")
    try:
        with urlopen(Request(url, headers=UA), timeout=180) as r:
            body = r.read()
    except (HTTPError, URLError) as e:
        sys.exit(f"FAILED {url}\n  {type(e).__name__}: {e}")
    # A GTFS feed is a zip of csv files. Validate before trusting it.
    try:
        with zipfile.ZipFile(io.BytesIO(body)) as z:
            names = z.namelist()
    except zipfile.BadZipFile as e:
        sys.exit(f"CORRUPT zip from {url}: {e}")
    if "stops.txt" not in names:
        sys.exit(f"{url} has no stops.txt; members were {names[:10]}")
    dest.write_bytes(body)
    print(f"  wrote {dest}  ({len(body):,} bytes, {len(names)} members)")
    return dest


def read_stops(path):
    with zipfile.ZipFile(path) as z:
        with z.open("stops.txt") as f:
            text = io.TextIOWrapper(f, encoding="utf-8-sig")
            return list(csv.DictReader(text))


def main():
    today = date.today().isoformat()
    rows = []
    for agency_id, agency_name, fname, url in FEEDS:
        path = fetch(fname, url)
        stops = read_stops(path)
        print(f"\n{agency_name}: {len(stops):,} stops in feed")

        kept = 0
        for s in stops:
            name = (s.get("stop_name") or "").strip()
            ltype = (s.get("location_type") or "0").strip() or "0"
            is_station = ltype == "1"
            is_named = bool(SERVICE_POINT_RE.search(name))
            if not (is_station or is_named):
                continue
            try:
                lat, lon = float(s["stop_lat"]), float(s["stop_lon"])
            except (KeyError, ValueError):
                continue
            rows.append({
                "agency_id": agency_id, "agency_name": agency_name,
                "sector": "transit",
                "location_id": f"{agency_id}-{s.get('stop_id','')}",
                "location_name": name,
                "location_type": "station" if is_station else "transit_center_or_park_ride",
                "lat": lat, "lon": lon,
                "gtfs_location_type": ltype,
                "capture_date": today,
                "source_url": url,
            })
            kept += 1
        print(f"  service points kept: {kept:,} "
              f"({100*kept/max(len(stops),1):.1f}% of stops)")

    df = pd.DataFrame(rows).drop_duplicates(subset=["agency_id", "location_id"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"\nwrote {OUT}  ({len(df):,} service points)")
    print("\nby agency and type:")
    print(pd.crosstab(df["agency_name"], df["location_type"], margins=True).to_string())


if __name__ == "__main__":
    main()
