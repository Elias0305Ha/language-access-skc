import pandas as pd

inv = pd.read_csv("data/inventory/school_inventory.csv")

for a, sub in inv.groupby("agency_name"):
    print("\n" + a)
    print(sub[["language", "families"]].to_string(index=False))

    