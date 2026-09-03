"""
Diagnose the Census API key without printing it to the terminal.

Prints the length and the first and last four characters only. A key is
still a secret; you should not paste a whole one into a chat window, a
screenshot, or a terminal someone might be looking over.
"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

env_path = Path(".env")

print("1. Does .env exist where Python is looking?")
print(f"   looking in: {Path.cwd()}")
print(f"   .env found: {env_path.exists()}")

# Windows editors love to append .txt
for stray in [".env.txt", "env", "env.txt"]:
    if Path(stray).exists():
        print(f"   WARNING: found a file named '{stray}'. "
              f"It should be exactly '.env'")

print("\n2. Does the key load?")
load_dotenv()
key = os.getenv("CENSUS_API_KEY")

if not key:
    raise SystemExit(
        "   CENSUS_API_KEY did not load.\n"
        "   The file should contain exactly one line, no quotes, no spaces:\n"
        "     CENSUS_API_KEY=yourkeyhere"
    )

print(f"   loaded: yes")
print(f"   length: {len(key)}  (a Census key is 40 characters)")
print(f"   looks like: {key[:4]}...{key[-4:]}")

if len(key) != 40:
    print("   WARNING: wrong length. Check for quotes, spaces, or a "
          "partial paste.")
if key != key.strip():
    print("   WARNING: leading or trailing whitespace in the key.")
if key.startswith(("'", '"')) or key.endswith(("'", '"')):
    print("   WARNING: the key has quotes around it. Remove them.")

print("\n3. Does the Census accept it?")
resp = requests.get(
    "https://api.census.gov/data/2024/acs/acs5",
    params={"get": "NAME", "for": "county:033", "in": "state:53", "key": key},
    timeout=60,
)

if "invalid_key" in resp.url or "Invalid Key" in resp.text:
    print("   REJECTED. The key is not active.")
    print("   Check your email for the activation link from the Census")
    print("   Bureau and click it. A key does not work until activated.")
elif resp.status_code == 200 and resp.text.strip().startswith("["):
    print("   ACCEPTED.")
    print(f"   test response: {resp.text.strip()[:120]}")
    print("\n   You are good. Run: python src/fetch_census.py")
else:
    print(f"   Unexpected response, HTTP {resp.status_code}")
    print(f"   {resp.text[:300]}")
