"""
Member 1 - Data & Features
Cleans the raw phishing dataset and produces data/processed/clean.csv

Rerunnable: safe to run this script as many times as you want on the same
raw file. It always regenerates data/processed/clean.csv from scratch.
"""

import os
import pandas as pd

RAW_PATH = "data/raw/PhiUSIIL_Phishing_URL_Dataset.csv"
URL_COLUMN = "URL"
LABEL_COLUMN = "label"

OUT_PATH = "data/processed/clean.csv"

# This raw dataset uses 1 = legitimate, 0 = phishing (opposite of our project).
# We invert it here so our output always means 0 = legitimate, 1 = phishing.
LABEL_MAP = {
    1: 0, "1": 0,   # raw legitimate -> project legitimate (0)
    0: 1, "0": 1,   # raw phishing   -> project phishing (1)
}


def load_raw(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"[1] Loaded {len(df)} rows from {path}")
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Step 1: strip leading/trailing whitespace from every URL
    df[URL_COLUMN] = df[URL_COLUMN].astype(str).str.strip()
    print(f"[2] After stripping whitespace: {len(df)} rows")

    # Step 2: drop rows where URL or label is empty/NaN
    before = len(df)
    df = df.dropna(subset=[URL_COLUMN, LABEL_COLUMN])
    df = df[df[URL_COLUMN] != ""]
    print(f"[3] After dropping empty URL/label rows: {len(df)} rows (dropped {before - len(df)})")

    # Step 3: drop exact duplicate URLs
    before = len(df)
    df = df.drop_duplicates(subset=[URL_COLUMN])
    print(f"[4] After dropping duplicate URLs: {len(df)} rows (dropped {before - len(df)})")

    # Step 4: map labels to integers (0 = legitimate, 1 = phishing)
    def map_label(val):
        key = str(val).strip().lower()
        if key in LABEL_MAP:
            return LABEL_MAP[key]
        return LABEL_MAP.get(val, None)

    df["label"] = df[LABEL_COLUMN].apply(map_label)
    before = len(df)
    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)
    print(f"[5] After mapping + dropping unmappable labels: {len(df)} rows (dropped {before - len(df)})")

    df = df.rename(columns={URL_COLUMN: "url"})[["url", "label"]]
    return df


def main():
    os.makedirs("data/processed", exist_ok=True)
    df = load_raw(RAW_PATH)
    cleaned = clean(df)
    cleaned.to_csv(OUT_PATH, index=False)

    print(f"\nSaved {len(cleaned)} rows to {OUT_PATH}")
    print("Class balance:")
    print(cleaned["label"].value_counts())


if __name__ == "__main__":
    main()