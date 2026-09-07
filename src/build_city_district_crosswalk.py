"""
Phase 4: build a city-to-school-district crosswalk, spatially.

Why this exists. Demand is measured by school district (OSPI). Supply in
the city sector is measured by city. To compare them, something has to
say which cities sit in which districts.

Doing that from knowledge is the same mistake that nearly deleted Skyway
from the library sector: city boundaries and school district boundaries
do not align anywhere in this study area. Highline School District covers
Burien, SeaTac, Des Moines, Normandy Park, White Center and Boulevard
Park, and is not a city. Federal Way School District includes part of Des
Moines. Renton School District includes Skyway, which has a Seattle
address.

So the crosswalk is computed by intersecting Census TIGER polygons and
reporting the OVERLAP AREA, not a yes/no. A city that is 3% inside a
district is not the same claim as a city that is 90% inside it, and the
gap index needs to weight accordingly.

Sources, both Census TIGER/Line 2024, same publisher and vintage as the
district polygons already frozen:
    tl_2024_53_place.zip  incorporated places (cities), Washington
    tl_2024_53_unsd.zip   unified school districts, Washington

Output: data/processed/city_district_overlap.csv
"""

import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import geopandas as gpd
import pandas as pd

RAW = Path("data/raw")
PLACES_NAME = "tl_2024_53_place.zip"
PLACES_URL = f"https://www2.census.gov/geo/tiger/TIGER2024/PLACE/{PLACES_NAME}"
DISTRICTS = RAW / "tl_2024_53_unsd.zip"
OUT = Path("data/processed/city_district_overlap.csv")

STUDY_DISTRICTS = [
    "Auburn School District", "Federal Way School District",
    "Highline School District", "Kent School District",
    "Renton School District", "Tukwila School District",
]

# The eight cities in the study area, as named in the city inventory.
STUDY_CITIES = ["Auburn", "Burien", "Des Moines", "Federal Way",
                "Kent", "Renton", "SeaTac", "Tukwila"]

# Area is meaningless in degrees. EPSG:2926 is Washington State Plane
# North (US feet), the standard projected CRS for this region. Overlap
# fractions computed in EPSG:4326 would be wrong by the cosine of the
# latitude and would look plausible while being wrong.
AREA_CRS = "EPSG:2926"


def fetch_places():
    dest = RAW / PLACES_NAME
    if dest.exists():
        print(f"skip  {PLACES_NAME}  (already on disk, {dest.stat().st_size:,} bytes)")
        return dest
    print(f"fetch {PLACES_URL}")
    try:
        req = Request(PLACES_URL, headers={"User-Agent": "language-access-skc/1.0"})
        with urlopen(req, timeout=120) as resp:
            body = resp.read()
    except (HTTPError, URLError) as e:
        sys.exit(f"FAILED {PLACES_URL}\n  {type(e).__name__}: {e}")
    dest.write_bytes(body)
    print(f"  wrote {dest}  ({len(body):,} bytes)")
    return dest


def main():
    places_zip = fetch_places()

    places = gpd.read_file(f"zip://{places_zip}")
    districts = gpd.read_file(f"zip://{DISTRICTS}")
    print(f"\nplaces in WA: {len(places)}   districts in WA: {len(districts)}")

    districts = districts[districts["NAME"].isin(STUDY_DISTRICTS)].copy()
    missing = sorted(set(STUDY_DISTRICTS) - set(districts["NAME"]))
    if missing:
        sys.exit(f"district not found in shapefile: {missing}")

    cities = places[places["NAME"].isin(STUDY_CITIES)].copy()
    found = sorted(cities["NAME"])
    print(f"study cities matched: {len(found)} of {len(STUDY_CITIES)}  {found}")
    absent = sorted(set(STUDY_CITIES) - set(found))
    if absent:
        # Do not silently proceed with a missing city.
        print(f"WARNING city not found in TIGER places: {absent}", file=sys.stderr)

    # Project once, explicitly, before any area is computed.
    cities = cities.to_crs(AREA_CRS)
    districts = districts.to_crs(AREA_CRS)
    print(f"projected both to {AREA_CRS} for area computation")

    cities["city_area"] = cities.geometry.area
    districts = districts[["GEOID", "NAME", "geometry"]].rename(
        columns={"GEOID": "district_geoid", "NAME": "district_name"})

    inter = gpd.overlay(
        cities[["NAME", "city_area", "geometry"]].rename(columns={"NAME": "city"}),
        districts, how="intersection")
    inter["overlap_area"] = inter.geometry.area
    inter["pct_of_city_in_district"] = (
        100 * inter["overlap_area"] / inter["city_area"]).round(1)

    out = (inter[["city", "district_name", "district_geoid",
                  "pct_of_city_in_district"]]
           .sort_values(["city", "pct_of_city_in_district"], ascending=[True, False])
           .reset_index(drop=True))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"\nwrote {OUT}  ({len(out)} city-district pairs)\n")

    for city, sub in out.groupby("city"):
        parts = ", ".join(f"{r.district_name.replace(' School District','')} "
                          f"{r.pct_of_city_in_district}%"
                          for r in sub.itertuples())
        total = sub["pct_of_city_in_district"].sum()
        flag = "" if total > 90 else f"   <- only {total:.0f}% of this city is inside the six study districts"
        print(f"  {city:12} {parts}{flag}")

    multi = out.groupby("city").size()
    print(f"\ncities split across more than one study district: "
          f"{sorted(multi[multi > 1].index.tolist())}")


if __name__ == "__main__":
    main()
