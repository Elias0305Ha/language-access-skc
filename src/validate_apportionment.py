"""
Phase 2: test the apportionment assumption.

THE ASSUMPTION UNDER TEST

Tract and district data give only broad language buckets. To get a specific
language you would take its share within its bucket, measured somewhere
coarse, and apply that share to a finer area. That step assumes the language
mix inside a bucket is roughly the same everywhere in the region.

This project's whole premise is that these communities cluster, which is the
same as saying the mix is NOT the same everywhere. So the method may assume
away the thing being measured. That has to be tested, not asserted.

TWO TESTS

  A. Internal, using PUMS alone. Compare each PUMA's within-bucket language
     mix against the regional mix. No outside data needed.

  B. External, using OSPI as ground truth. Apply the regional mix to each
     district and compare the predicted language shares against what OSPI
     actually observed.

Test B compares SHARES, not counts, on purpose. OSPI counts families with
school-age children; the ACS counts all people aged 5 and over. The
denominators are different, so raw counts are not comparable. Shares within
a bucket are.
"""

from pathlib import Path
import pandas as pd

# Which C16001 bucket each specific language falls into.
# The three "Other" buckets are where this project's languages hide.
BUCKET = {
    "Spanish": "Spanish",
    "Vietnamese": "Vietnamese",
    "Korean": "Korean",
    "Arabic": "Arabic",
    "Tagalog": "Tagalog", "Filipino": "Tagalog", "Ilocano": "Tagalog",
    "Chinese": "Chinese", "Cantonese": "Chinese", "Mandarin": "Chinese",
    "French": "French/Haitian/Cajun", "Haitian": "French/Haitian/Cajun",
    "German": "German/West Germanic",
    "Russian": "Russian/Polish/Slavic", "Ukrainian": "Russian/Polish/Slavic",
    "Polish": "Russian/Polish/Slavic", "Serbo-Croatian": "Russian/Polish/Slavic",
    # Indo-European languages with no bucket of their own
    "Dari": "Other Indo-European", "Pashto": "Other Indo-European",
    "Farsi": "Other Indo-European", "Persian": "Other Indo-European",
    "Punjabi": "Other Indo-European", "Hindi": "Other Indo-European",
    "Urdu": "Other Indo-European", "Nepali": "Other Indo-European",
    "Portuguese": "Other Indo-European", "Gujarati": "Other Indo-European",
    "Bengali": "Other Indo-European", "Romanian": "Other Indo-European",
    "Italian": "Other Indo-European", "Greek": "Other Indo-European",
    "Armenian": "Other Indo-European",
    # Asian and Pacific Island languages with no bucket of their own
    "Marshallese": "Other Asian & Pacific Island",
    "Chuukese": "Other Asian & Pacific Island",
    "Samoan": "Other Asian & Pacific Island",
    "Chamorro": "Other Asian & Pacific Island",
    "Hawaiian": "Other Asian & Pacific Island",
    "Tongan": "Other Asian & Pacific Island",
    "Khmer": "Other Asian & Pacific Island",
    "Cambodian": "Other Asian & Pacific Island",
    "Burmese": "Other Asian & Pacific Island",
    "Thai": "Other Asian & Pacific Island",
    "Lao": "Other Asian & Pacific Island",
    "Hmong": "Other Asian & Pacific Island",
    "Japanese": "Other Asian & Pacific Island",
    "Indonesian": "Other Asian & Pacific Island",
    "Telugu": "Other Asian & Pacific Island",
    "Tamil": "Other Asian & Pacific Island",
    "Malayalam": "Other Asian & Pacific Island",
    # Afro-Asiatic and African languages, minus Arabic
    "Amharic": "Other and unspecified",
    "Tigrinya": "Other and unspecified",
    "Oromo": "Other and unspecified",
    "Somali": "Other and unspecified",
    "Swahili": "Other and unspecified",
    "Hebrew": "Other and unspecified",
    "Yoruba": "Other and unspecified",
    "Igbo": "Other and unspecified",
    "Wolof": "Other and unspecified",
    "Kinyarwanda": "Other and unspecified",
    "Maay Maay": "Other and unspecified",
    # Additional Slavic
    "Bosnian": "Russian/Polish/Slavic", "Croatian": "Russian/Polish/Slavic",
    "Serbian": "Russian/Polish/Slavic", "Bulgarian": "Russian/Polish/Slavic",
    "Czech": "Russian/Polish/Slavic", "Slovak": "Russian/Polish/Slavic",
    "Slovene": "Russian/Polish/Slavic", "Macedonian": "Russian/Polish/Slavic",
    # Additional Indo-European with no bucket of their own
    "Albanian": "Other Indo-European", "Irish": "Other Indo-European",
    "Lithuanian": "Other Indo-European", "Latvian": "Other Indo-European",
    "Marathi": "Other Indo-European", "Sinhala": "Other Indo-European",
    "Pahari": "Other Indo-European", "Kashmiri": "Other Indo-European",
    "India N.E.C.": "Other Indo-European",
    # Additional West Germanic
    "Dutch": "German/West Germanic", "Afrikaans": "German/West Germanic",
    "Yiddish": "German/West Germanic", "Pennsylvania German": "German/West Germanic",
    # Additional Austronesian and Asian
    "Cebuano": "Tagalog", "Bisayan": "Tagalog",
    "Chin languages": "Other Asian & Pacific Island",
    "IuMien": "Other Asian & Pacific Island",
    "Mien": "Other Asian & Pacific Island",
    "Karen languages": "Other Asian & Pacific Island",
    "Kannada": "Other Asian & Pacific Island",
    "Nepali": "Other Indo-European",
    "Fijian": "Other Asian & Pacific Island",
    "Chamic": "Other Asian & Pacific Island",
    "Malay": "Other Asian & Pacific Island",
    "Mongolian": "Other Asian & Pacific Island",
    # Turkic, Uralic and other non-Indo-European
    "Turkish": "Other and unspecified", "Uzbek": "Other and unspecified",
    "Kazakh": "Other and unspecified", "Hungarian": "Other and unspecified",
    "Finnish": "Other and unspecified", "Estonian": "Other and unspecified",
    "Georgian": "Other and unspecified",
    # Additional African languages
    "Akan (including Twi)": "Other and unspecified",
    "Fulah": "Other and unspecified", "Ganda": "Other and unspecified",
    "Gbe languages": "Other and unspecified", "Krio": "Other and unspecified",
    "Shona": "Other and unspecified", "Zulu": "Other and unspecified",
    "Xhosa": "Other and unspecified", "Chichewa": "Other and unspecified",
    "Manding languages": "Other and unspecified",
    "Nilo-Saharan languages": "Other and unspecified",
    "Other Afro-Asiatic languages": "Other and unspecified",
    "Other Bantu languages": "Other and unspecified",
    "Other African languages": "Other and unspecified",
}

# The buckets where apportionment is actually needed. The rest are
# published directly at tract and district level, so no estimating.
RESIDUAL = ["Other Indo-European", "Other Asian & Pacific Island",
            "Other and unspecified", "Russian/Polish/Slavic"]

Path("outputs").mkdir(exist_ok=True)


def to_bucket(s):
    return s.map(BUCKET)


# --- load ------------------------------------------------------------

pums = pd.read_csv("data/processed/pums_language_by_puma.csv")
ospi = pd.read_csv("data/processed/demand_by_district.csv")

pums["bucket"] = to_bucket(pums["language"])
ospi["clean"] = ospi["language"].str.replace("Chinese-", "", regex=False)
ospi["bucket"] = to_bucket(ospi["clean"])

unmapped = pums.loc[pums["bucket"].isna(), "language"].unique()
print(f"PUMS languages with no bucket assigned: {len(unmapped)}")
if len(unmapped):
    print("  " + ", ".join(sorted(unmapped)[:20]))
print("  (these are excluded from the test, not silently binned)\n")

pums = pums.dropna(subset=["bucket"])
ospi = ospi.dropna(subset=["bucket"])


# --- TEST A: does each PUMA match the region? ------------------------

print("=" * 74)
print("TEST A. PUMS internal. Within-bucket share, each PUMA vs the region.")
print("=" * 74)

regional = (pums.groupby(["bucket", "language"])["people"].sum()
            .reset_index())
regional["regional_share"] = (regional["people"]
                              / regional.groupby("bucket")["people"]
                              .transform("sum"))

by_puma = pums.copy()
by_puma["puma_share"] = (by_puma["people"]
                         / by_puma.groupby(["puma", "bucket"])["people"]
                         .transform("sum"))

test_a = by_puma.merge(regional[["bucket", "language", "regional_share"]],
                       on=["bucket", "language"], how="left")
test_a["error_pp"] = (test_a["puma_share"] - test_a["regional_share"]) * 100

resid = test_a[test_a["bucket"].isin(RESIDUAL)]

summary_a = (resid.groupby("language")
             .agg(regional_share=("regional_share", "first"),
                  min_puma_share=("puma_share", "min"),
                  max_puma_share=("puma_share", "max"),
                  worst_error_pp=("error_pp", lambda s: s.abs().max()))
             .sort_values("worst_error_pp", ascending=False))

print("\nAll figures are percentages. If the assumption held, min and max")
print("would both sit close to the regional share.\n")
disp = summary_a.head(15).copy()
for c in ["regional_share", "min_puma_share", "max_puma_share"]:
    disp[c] = (disp[c] * 100).round(1)
disp["worst_error_pp"] = disp["worst_error_pp"].round(1)
print(disp.to_string())

mae_a = resid["error_pp"].abs().mean()
print(f"\nMean absolute error across all residual-bucket languages: "
      f"{mae_a:.1f} percentage points")


# --- TEST B: does the region predict each district? ------------------

print("\n" + "=" * 74)
print("TEST B. OSPI ground truth. Predicted share vs observed share.")
print("=" * 74)

ospi_share = ospi.copy()
ospi_share["observed_share"] = (
    ospi_share["families"]
    / ospi_share.groupby(["DistrictName", "bucket"])["families"]
    .transform("sum"))

test_b = ospi_share.merge(
    regional[["bucket", "language", "regional_share"]],
    left_on=["bucket", "clean"], right_on=["bucket", "language"],
    how="inner", suffixes=("", "_pums"))

test_b["error_pp"] = (test_b["observed_share"]
                      - test_b["regional_share"]) * 100

test_b = test_b[test_b["bucket"].isin(RESIDUAL)]

out = (test_b[["DistrictName", "bucket", "clean", "families",
               "observed_share", "regional_share", "error_pp"]]
       .rename(columns={"clean": "language"})
       .sort_values("error_pp", key=abs, ascending=False))

out.to_csv("outputs/apportionment_validation.csv", index=False)

print("\nWorst 20 misses. error_pp is percentage points off.\n")
show = out.head(20).copy()
show["observed_share"] = (show["observed_share"] * 100).round(1)
show["regional_share"] = (show["regional_share"] * 100).round(1)
show["error_pp"] = show["error_pp"].round(1)
show["DistrictName"] = show["DistrictName"].str.replace(
    " School District", "", regex=False)
print(show.to_string(index=False))

mae_b = out["error_pp"].abs().mean()
print(f"\nMean absolute error: {mae_b:.1f} percentage points")
print(f"Rows tested: {len(out)}")

print("\nwrote outputs/apportionment_validation.csv")
