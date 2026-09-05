"""
Phase 3: turn the frozen KCLS locations JSON into a locations table,
with each branch assigned to a school district by point-in-polygon.

Why not filter on the city name the API gives:
  Four KCLS branches (White Center, Boulevard Park, Greenbridge, Skyway)
  carry a 'Seattle' mailing city because they sit in unincorporated King
  County. Three of them are inside Highline School District and one is
  inside Renton School District. A city-name filter drops all four
  silently. Skyway is one of only two branches in the county holding
  Amharic material, so that filter would have halved the Amharic result.

  School district boundaries do not follow city boundaries anywhere in
  this study area. Geography is the only correct key.

Output: data/processed/kcls_locations.csv
"""

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

RAW = Path("data/raw")
OUT = Path("data/processed/kcls_locations.csv")

STUDY_DISTRICTS = [
    "Auburn School District",
    "Federal Way School District",
    "Highline School District",
    "Kent School District",
    "Renton School District",
    "Tukwila School District",
]

# Everything gets compared in one CRS, stated out loud.
# 4326 is what the KCLS API emits (standard GPS lat/lon).
WORKING_CRS = "EPSG:4326"

# Not every "location" is a staffed library. A locker cannot lend you an
# interpreter. These are flagged, not dropped, so the count reconciles
# and so a reviewer can see the judgment instead of guessing at it.
TYPE_RULES = [
    ("closed",      lambda n: "closed" in n.lower()),
    ("locker",      lambda n: "locker" in n.lower()),
    ("admin",       lambda n: "administrative" in n.lower() or "service center" in n.lower()),
    ("express",     lambda n: "express" in n.lower()),
]


def classify(name):
    for label, test in TYPE_RULES:
        if test(name):
            return label
    return "branch"


def clean_name(raw):
    """'Kent Closed. Holds Pickup at Kent Panther Lake.' -> 'Kent'

    KCLS puts operational status inside the name field. Keep the raw
    string in its own column; never overwrite the source value.
    """
    return raw.split(".")[0].replace("Closed", "").strip()


def main():
    # ---- 1. read the frozen JSON -------------------------------------
    with open(RAW / "kcls_locations.json", encoding="utf-8") as f:
        payload = json.load(f)

    ents = payload["entities"]["locations"]
    print(f"locations in frozen JSON: {len(ents)}")

    rows = []
    no_coords = []
    for loc_id, v in ents.items():
        addr = v.get("address") or {}
        pt = (v.get("mapLocation") or {}).get("centrePoint") or {}
        lat, lon = pt.get("lat"), pt.get("lng")

        if lat is None or lon is None:
            no_coords.append(v.get("name"))
            continue

        raw_name = v.get("name", "")
        rows.append({
            "agency_id": "kcls",
            "location_id": f"kcls-{loc_id}",
            "location_name": clean_name(raw_name),
            "location_name_raw": raw_name,
            "location_type": classify(raw_name),
            "street": f"{addr.get('number','')} {addr.get('street','')}".strip(),
            "city": addr.get("city"),
            "state": addr.get("state"),
            "zip": addr.get("zip"),
            "lat": lat,
            "lon": lon,
            "web_url": v.get("webUrl"),
        })

    # Announce what was excluded rather than letting the total shrink.
    if no_coords:
        print(f"EXCLUDED {len(no_coords)} with no coordinates: {no_coords}")

    df = pd.DataFrame(rows)
    print(f"locations with coordinates: {len(df)}")
    print("\nlocation_type counts:")
    print(df["location_type"].value_counts().to_string())
    flagged = df[df["location_type"] != "branch"]
    if len(flagged):
        print("\nflagged as not a staffed branch (verify these by eye):")
        print(flagged[["location_name_raw", "location_type"]].to_string(index=False))

    # ---- 2. points ---------------------------------------------------
    # Build geometry explicitly and STATE the CRS. A GeoDataFrame with
    # crs=None will happily join against anything and give you garbage.
    pts = gpd.GeoDataFrame(
        df,
        geometry=[Point(xy) for xy in zip(df["lon"], df["lat"])],  # x=lon, y=lat
        crs=WORKING_CRS,
    )

    # ---- 3. polygons -------------------------------------------------
    districts = gpd.read_file(f"zip://{RAW / 'tl_2024_53_unsd.zip'}")
    print(f"\ndistrict polygons in shapefile: {len(districts)}  CRS: {districts.crs}")

    districts = districts[districts["NAME"].isin(STUDY_DISTRICTS)].copy()
    found = sorted(districts["NAME"])
    missing = sorted(set(STUDY_DISTRICTS) - set(found))
    print(f"study districts matched: {len(found)}")
    if missing:
        raise SystemExit(f"district name not found in shapefile: {missing}")

    # Convert, do not assume. See the CRS note in the docstring.
    districts = districts.to_crs(WORKING_CRS)
    districts = districts[["GEOID", "NAME", "geometry"]].rename(
        columns={"GEOID": "district_geoid", "NAME": "district_name"}
    )

    # ---- 4. point in polygon ----------------------------------------
    # predicate='within': keep the point, attach the polygon that contains it.
    # how='left': keep every branch, including ones outside all six
    # districts, so the row count is conserved and the misses are visible.
    joined = gpd.sjoin(pts, districts, how="left", predicate="within")

    # A point on a shared district border could match two polygons and
    # duplicate the row. Check rather than hope.
    if len(joined) != len(pts):
        dupes = joined[joined.index.duplicated(keep=False)]
        print(f"\nWARNING sjoin changed the row count {len(pts)} -> {len(joined)}")
        print(dupes[["location_name", "district_name"]].to_string())

    joined["in_study_area"] = joined["district_name"].notna()

    out = pd.DataFrame(joined.drop(columns=["geometry", "index_right"]))

    print(f"\nin study area:     {int(out['in_study_area'].sum())}")
    print(f"outside study area: {int((~out['in_study_area']).sum())}")
    print("\nbranches per district:")
    print(out[out["in_study_area"]]["district_name"].value_counts().to_string())

    print("\nSANITY CHECK, the four Seattle-addressed branches:")
    seattle = out[out["city"] == "Seattle"][["location_name", "city", "district_name"]]
    print(seattle.to_string(index=False))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"\nwrote {OUT}  ({len(out)} rows)")


if __name__ == "__main__":
    main()
