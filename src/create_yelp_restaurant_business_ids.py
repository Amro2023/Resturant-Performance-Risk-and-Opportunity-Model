import pandas as pd
from pathlib import Path

# Project paths
project_root = Path(__file__).resolve().parents[1]

business_raw_path = project_root / "data" / "raw" / "yelp" / "yelp_academic_dataset_business.json"
restaurant_output_path = project_root / "data" / "processed" / "yelp_us_restaurants.csv"
business_ids_output_path = project_root / "data" / "processed" / "yelp_us_restaurant_business_ids.csv"

# U.S. states
us_states = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
    "DC"
]

print("Loading Yelp business file...")

df_business = pd.read_json(business_raw_path, lines=True)

print(f"Raw business records: {len(df_business):,}")

# Filter to U.S. restaurants
df_restaurants = df_business[
    df_business["categories"].notna()
    & df_business["categories"].str.contains("Restaurants", case=False, na=False)
    & df_business["state"].isin(us_states)
].copy()

print(f"Filtered U.S. restaurants: {len(df_restaurants):,}")
print(f"States represented: {df_restaurants['state'].nunique()}")

# Save full filtered restaurant file
df_restaurants.to_csv(restaurant_output_path, index=False)

# Save business IDs only
df_restaurants[["business_id"]].to_csv(business_ids_output_path, index=False)

print("Saved restaurant file to:")
print(restaurant_output_path)

print("Saved business ID file to:")
print(business_ids_output_path)