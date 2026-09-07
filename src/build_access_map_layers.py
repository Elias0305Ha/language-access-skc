"""
Phase 4: build the map layers. Physical service points, the languages
each one serves, and the district-language pairs with no point at all.

Two layers come out of this:

  service_points.csv        one row per physical location, with the
                            languages that location serves at tier 3
  access_deserts.csv        (district, language) pairs with measured
                            demand and NO physical service point serving
                            that language anywhere inside the district

The distinction that matters. Earlier phases measured whether an agency
publishes anything in a language. This measures whether a person can
WALK INTO A BUILDING inside their own district and be served in it. A
statewide PDF is not a building.

Coverage is partial and the output says so. Library branches and transit
service points are here because both publish machine-readable locations.
Schools, cities, clinics, food banks and legal aid do not, and their
addresses have not been collected. So an "access desert" here means no
LIBRARY OR TRANSIT point serving that language in the district, which is
a floor on the true picture, not the whole of it. The column
sectors_covered records exactly which sectors the claim rests on.

Output: data/processed/service_points.csv
        outputs/access_deserts.csv
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

RAW = Path("data/raw")
DISTRICT_ZIP = RAW / "tl_2024_53_unsd.zip"
OUT_POINTS = Path("data/processed/service_points.csv")
OUT_DESERTS = Path("outputs/access_deserts.csv")

WORKING_CRS = "EPSG:4326"
STUDY_DISTRICTS = ["Auburn School District", "Federal Way School District",
                   "Highline School District", "Kent School District",
                   "Renton School District", "Tukwila School District"]

# Sectors represented in this layer. Stated explicitly because the
# access-desert claim is only as wide as this list.
SECTORS_COVERED = ["library", "transit"]


def assign_districts(df, lat="lat", lon="lon"):
    pts = gpd.GeoDataFrame(
        df, geometry=[Point(xy) for xy in zip(df[lon], df[lat])],
        crs=WORKING_CRS)
    d = gpd.read_file(f"zip://{DISTRICT_ZIP}")
    d = d[d["NAME"].isin(STUDY_DISTRICTS)].to_crs(WORKING_CRS)
    d = d[["GEOID", "NAME", "geometry"]].rename(
        columns={"GEOID": "district_geoid", "NAME": "district_name"})
    joined = gpd.sjoin(pts, d, how="left", predicate="within")
    if len(joined) != len(pts):
        # A point on a shared border can match two polygons.
        joined = joined[~joined.index.duplicated(keep="first")]
        print(f"  NOTE: dropped duplicate border matches, kept {len(joined)}")
    return pd.DataFrame(joined.drop(columns=["geometry", "index_right"]))


def main():
    # ---- library branches, with per-branch collections ----------------
    lib = pd.read_csv("data/processed/kcls_locations.csv")
    lib = lib[lib["in_study_area"] & (lib["location_type"] == "branch")].copy()
    coll = pd.read_csv("data/processed/kcls_collections.csv")
    coll = coll[coll["is_physical"].astype(str).str.lower() == "true"]
    lmap = pd.read_csv("data/reference/kcls_language_map.csv")
    lmap["modes"] = lmap["applies_to_modes"].str.split(",").apply(
        lambda xs: {x.strip() for x in xs})

    def label_en(lbl):
        for sep in ("–", "—", " - "):
            if sep in lbl:
                return lbl.split(sep)[-1].strip()
        return lbl.strip()

    coll_canon = {}
    for _, r in lmap.iterrows():
        if "collection" in r["modes"]:
            coll_canon.setdefault(label_en(r["kcls_label"]), []).append(r["canonical_name"])

    branch_langs = {}
    for _, r in coll.iterrows():
        for canon in coll_canon.get(r["language_english"], []):
            branch_langs.setdefault(r["location_name"], set()).add(canon)

    lib_rows = []
    for r in lib.itertuples():
        lib_rows.append({
            "agency_id": "kcls", "agency_name": "King County Library System",
            "sector": "library", "location_id": r.location_id,
            "location_name": r.location_name, "location_type": "library_branch",
            "lat": r.lat, "lon": r.lon,
            "district_name": r.district_name,
            "languages_served": "; ".join(sorted(branch_langs.get(r.location_name, []))),
        })
    libdf = pd.DataFrame(lib_rows)
    print(f"library branches in study area: {len(libdf)}")

    # ---- transit service points --------------------------------------
    tr = pd.read_csv("data/processed/transit_service_points.csv")
    print(f"transit service points, region-wide: {len(tr):,}")
    tr = assign_districts(tr)
    tr = tr[tr["district_name"].notna()].copy()
    print(f"  inside the six study districts: {len(tr):,}")

    # Transit language coverage is agency-level: every Metro point offers
    # what Metro offers. Taken from the master inventory at tier 3.
    inv = pd.read_csv("data/processed/master_inventory.csv")
    inv["written_tier"] = pd.to_numeric(inv["written_tier"], errors="coerce")
    t3 = inv[(inv["written_tier"] == 3)]
    agency_langs = t3.groupby("agency_id")["language"].apply(
        lambda s: sorted(set(s))).to_dict()

    tr["agency_name"] = tr["agency_name"]
    tr["languages_served"] = tr["agency_id"].map(
        lambda a: "; ".join(agency_langs.get(a, [])))
    trdf = tr[["agency_id", "agency_name", "sector", "location_id",
               "location_name", "location_type", "lat", "lon",
               "district_name", "languages_served"]]

    points = pd.concat([libdf, trdf], ignore_index=True)
    points["sectors_covered"] = ", ".join(SECTORS_COVERED)
    OUT_POINTS.parent.mkdir(parents=True, exist_ok=True)
    points.to_csv(OUT_POINTS, index=False)
    print(f"\nwrote {OUT_POINTS}  ({len(points):,} points)")
    print(points.groupby(["district_name", "sector"]).size().to_string())

    # ---- access deserts ----------------------------------------------
    demand = pd.read_csv("data/processed/demand_by_district.csv")
    served = {}
    for r in points.itertuples():
        if not r.languages_served:
            continue
        for lang in str(r.languages_served).split("; "):
            served.setdefault((r.district_name, lang), []).append(r.location_name)

    rows = []
    for r in demand.itertuples():
        key = (r.DistrictName, r.language)
        pts = served.get(key, [])
        rows.append({
            "district": r.DistrictName, "language": r.language,
            "families": r.families,
            "service_points_serving_language": len(pts),
            "is_access_desert": len(pts) == 0,
            "example_points": "; ".join(sorted(set(pts))[:4]),
            "sectors_covered": ", ".join(SECTORS_COVERED),
        })
    des = pd.DataFrame(rows).sort_values("families", ascending=False)
    des.to_csv(OUT_DESERTS, index=False)
    print(f"\nwrote {OUT_DESERTS}  ({len(des)} district-language pairs)")

    d = des[des["is_access_desert"]]
    print(f"\naccess deserts: {len(d)} of {len(des)} district-language pairs")
    print(f"families in them: {d['families'].sum():,} of {des['families'].sum():,}")
    print("\nlargest access deserts (no library or transit point serving "
          "the language in the district):")
    print(d.head(15)[["district", "language", "families"]].to_string(index=False))

    print("\ndistrict-language pairs that ARE served, by families:")
    s = des[~des["is_access_desert"]]
    print(s.head(10)[["district", "language", "families",
                      "service_points_serving_language"]].to_string(index=False))


if __name__ == "__main__":
    main()
