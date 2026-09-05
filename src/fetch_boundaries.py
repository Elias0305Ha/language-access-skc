"""
Phase 3: freeze the school district boundary polygons.

Source: Census TIGER/Line 2024, "Unified School District" (UNSD), Washington.

Why TIGER and not a King County GIS file:
  The ACS district-level pull in Phase 2 used the Census geography
  'school district (unified)'. TIGER UNSD is the polygon version of that
  exact same geography, from the same publisher, for the same year. So a
  district polygon here and a district row in the ACS data mean the same
  thing by construction, not by hopeful name matching.

We keep the .zip exactly as downloaded. GeoPandas reads a zipped
shapefile directly, so there is no reason to unpack it and no reason to
let an unpack step become a place where files drift.
"""

import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

RAW = Path("data/raw")
NAME = "tl_2024_53_unsd.zip"
URL = f"https://www2.census.gov/geo/tiger/TIGER2024/UNSD/{NAME}"

# A shapefile is not one file. It is a set that must travel together:
#   .shp  the geometry
#   .dbf  the attribute table
#   .shx  an index linking the two
#   .prj  the coordinate reference system
# Lose the .prj and your polygons are numbers with no stated units.
# This is the main reason shapefiles are distributed zipped.
EXPECTED_MEMBERS = {".shp", ".dbf", ".shx", ".prj"}


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    dest = RAW / NAME

    if dest.exists():
        print(f"skip  {NAME}  (already on disk, {dest.stat().st_size:,} bytes)")
    else:
        print(f"fetch {URL}")
        try:
            req = Request(URL, headers={"User-Agent": "language-access-skc/1.0"})
            with urlopen(req, timeout=120) as resp:
                body = resp.read()
        except (HTTPError, URLError) as e:
            print(f"  FAILED {URL}\n  {type(e).__name__}: {e}", file=sys.stderr)
            sys.exit(1)

        dest.write_bytes(body)
        print(f"  wrote {dest}  ({len(body):,} bytes)")

    # Verify the archive is complete before anything downstream trusts it.
    # A truncated download is still a file, and still opens.
    import zipfile
    try:
        with zipfile.ZipFile(dest) as z:
            names = z.namelist()
            bad = z.testzip()
    except zipfile.BadZipFile as e:
        print(f"  CORRUPT zip: {e}\n  delete {dest} and rerun", file=sys.stderr)
        sys.exit(1)

    if bad is not None:
        print(f"  CORRUPT member: {bad}\n  delete {dest} and rerun", file=sys.stderr)
        sys.exit(1)

    suffixes = {Path(n).suffix.lower() for n in names}
    missing = EXPECTED_MEMBERS - suffixes
    print(f"  archive contains {len(names)} members: {sorted(suffixes)}")
    if missing:
        print(f"  WARNING missing expected members: {sorted(missing)}", file=sys.stderr)
    else:
        print("  all required shapefile members present")


if __name__ == "__main__":
    main()
