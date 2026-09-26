"""
Member 1 - Data & Features
Loops the feature extractor over the cleaned dataset and produces the two
files everything else depends on:
    data/processed/train_features.csv
    data/processed/test_features.csv

Run this AFTER clean_data.py has produced data/processed/clean.csv.
"""

import pandas as pd
from sklearn.model_selection import train_test_split

from ml.features import extract_features, FEATURE_ORDER

CLEAN_PATH = "data/processed/clean.csv"
TRAIN_OUT = "data/processed/train_features.csv"
TEST_OUT = "data/processed/test_features.csv"


def build_matrix(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        feats = extract_features(row["url"])
        feats["label"] = int(row["label"])
        rows.append(feats)
    return pd.DataFrame(rows, columns=FEATURE_ORDER + ["label"])


def main():
    df = pd.read_csv(CLEAN_PATH)
    print(f"Loaded {len(df)} cleaned rows")

    train_df, test_df = train_test_split(
        df, test_size=0.2, stratify=df["label"], random_state=42
    )
    print(f"Split: {len(train_df)} train, {len(test_df)} test")

    train_matrix = build_matrix(train_df)
    test_matrix = build_matrix(test_df)

    train_matrix.to_csv(TRAIN_OUT, index=False)
    test_matrix.to_csv(TEST_OUT, index=False)

    print(f"Saved {TRAIN_OUT}  shape={train_matrix.shape}")
    print(f"Saved {TEST_OUT}   shape={test_matrix.shape}")
    print("\nTell your teammate now — this file existing is the single")
    print("most time-critical thing you do in the whole project.")


if __name__ == "__main__":
    main()