import json
import pandas as pd
from pathlib import Path
from collections import defaultdict

# Project paths
project_root = Path(__file__).resolve().parents[1]

filtered_review_path = project_root / "data" / "processed" / "yelp_us_restaurant_reviews_filtered.jsonl"
sampled_output_path = project_root / "data" / "processed" / "yelp_us_restaurant_reviews_sampled_100_per_business.csv"

max_reviews_per_business = 100

review_counts = defaultdict(int)
sampled_reviews = []

total_reviews = 0
kept_reviews = 0

print("Sampling reviews...")

with open(filtered_review_path, "r", encoding="utf-8") as infile:
    for line in infile:
        total_reviews += 1
        review = json.loads(line)

        business_id = review.get("business_id")

        if review_counts[business_id] < max_reviews_per_business:
            sampled_reviews.append({
                "review_id": review.get("review_id"),
                "business_id": business_id,
                "user_id": review.get("user_id"),
                "stars": review.get("stars"),
                "useful": review.get("useful"),
                "funny": review.get("funny"),
                "cool": review.get("cool"),
                "text": review.get("text"),
                "date": review.get("date")
            })

            review_counts[business_id] += 1
            kept_reviews += 1

        if total_reviews % 500000 == 0:
            print(f"Read {total_reviews:,} reviews | Kept {kept_reviews:,}")

df_sampled = pd.DataFrame(sampled_reviews)

df_sampled.to_csv(sampled_output_path, index=False)

print("Done.")
print(f"Total filtered reviews read: {total_reviews:,}")
print(f"Sampled reviews kept: {kept_reviews:,}")
print(f"Businesses represented: {df_sampled['business_id'].nunique():,}")
print(f"Saved to: {sampled_output_path}")