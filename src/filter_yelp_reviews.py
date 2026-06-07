import json
import pandas as pd
from pathlib import Path

# Paths
project_root = Path(__file__).resolve().parents[1]

business_ids_path = project_root / "data" / "processed" / "yelp_us_restaurant_business_ids.csv"
review_raw_path = project_root / "data" / "raw" / "yelp" / "yelp_academic_dataset_review.json"
review_output_path = project_root / "data" / "processed" / "yelp_us_restaurant_reviews_filtered.jsonl"

# Load restaurant business IDs
restaurant_ids = set(pd.read_csv(business_ids_path)["business_id"])

print(f"Loaded {len(restaurant_ids):,} restaurant business IDs")

matched_reviews = 0
total_reviews = 0

with open(review_raw_path, "r", encoding="utf-8") as infile, open(review_output_path, "w", encoding="utf-8") as outfile:
    for line in infile:
        total_reviews += 1
        review = json.loads(line)

        if review.get("business_id") in restaurant_ids:
            outfile.write(json.dumps(review) + "\n")
            matched_reviews += 1

        if total_reviews % 500000 == 0:
            print(f"Processed {total_reviews:,} reviews | Matched {matched_reviews:,}")

print("Done.")
print(f"Total reviews processed: {total_reviews:,}")
print(f"Matched restaurant reviews: {matched_reviews:,}")
print(f"Saved to: {review_output_path}")