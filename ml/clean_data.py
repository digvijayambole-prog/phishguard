"""
Member 1 - Data & Features
Cleans the raw datasets and produces data/processed/clean.csv

Sources:
  - Kaggle Malicious URLs dataset (benign + phishing rows only)
  - Tranco top-sites list (extra legitimate bare domains)

Rerunnable: always regenerates data/processed/clean.csv from scratch.
"""

import os
import pandas as pd

RAW_PATH = "data/raw/malicious_phish.csv"
URL_COLUMN = "url"
LABEL_COLUMN = "type"

TRANCO_PATH = "data/raw/tranco.csv"   # rank,domain (no header)
TRANCO_ROWS = 500000                  # candidate pool: top 500k domains

OUT_PATH = "data/processed/clean.csv"

# 4 classes in the Kaggle file: benign, phishing, defacement, malware.
# Keep only benign (legitimate = 0) and phishing (1); the rest are dropped.
LABEL_MAP = {
    "benign": 0,
    "phishing": 1,
}


def load_raw(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"[1] Loaded {len(df)} rows from {path}")
    return df


def load_tranco(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found - download the Tranco list first")
    t = pd.read_csv(path, header=None, names=["rank", "domain"], nrows=TRANCO_ROWS)
    t = t.dropna(subset=["domain"])
    t = t[t["domain"].astype(str).str.lower() != "domain"]  # in case a header row exists
    out = pd.DataFrame({"url": t["domain"].astype(str).str.strip(), "label": 0})
    print(f"[1b] Loaded {len(out)} Tranco domains (legitimate, bare) from {path}")
    return out


def clean(df: pd.DataFrame, tranco: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Step 2: strip whitespace
    df[URL_COLUMN] = df[URL_COLUMN].astype(str).str.strip()
    print(f"[2] After stripping whitespace: {len(df)} rows")

    # Step 2b: remove http(s):// scheme. In the Kaggle file the scheme is a
    # collection artifact (92% of legit URLs have none, 26% of phishing do).
    df[URL_COLUMN] = df[URL_COLUMN].str.replace(r"^https?://", "", case=False, regex=True)
    print(f"[2b] After removing http(s):// scheme: {len(df)} rows")

    # Step 2c: remove a leading "www." (39% of phishing rows vs 3% of legit).
    df[URL_COLUMN] = df[URL_COLUMN].str.replace(r"^www\.", "", case=False, regex=True)
    print(f"[2c] After removing leading www.: {len(df)} rows")

    # Step 3: drop empty URL/label rows
    before = len(df)
    df = df.dropna(subset=[URL_COLUMN, LABEL_COLUMN])
    df = df[df[URL_COLUMN] != ""]
    print(f"[3] After dropping empty URL/label rows: {len(df)} rows (dropped {before - len(df)})")

    # Step 4: drop exact duplicate URLs
    before = len(df)
    df = df.drop_duplicates(subset=[URL_COLUMN])
    print(f"[4] After dropping duplicate URLs: {len(df)} rows (dropped {before - len(df)})")

    # Step 5: map labels (0 = legitimate, 1 = phishing); drop other classes
    df["label"] = df[LABEL_COLUMN].apply(lambda v: LABEL_MAP.get(str(v).strip().lower(), None))
    before = len(df)
    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)
    df = df.rename(columns={URL_COLUMN: "url"})[["url", "label"]]
    print(f"[5] After mapping + dropping unmappable labels: {len(df)} rows (dropped {before - len(df)})")

    # Step 5b: add Tranco bare domains to the legitimate pool. The Kaggle file
    # has only ~100 legitimate bare domains, so without this the model would
    # learn "bare domain = phishing".
    before = len(df)
    df = pd.concat([df, tranco], ignore_index=True).drop_duplicates(subset=["url"])
    print(f"[5b] After adding Tranco domains + de-duplicating: {len(df)} rows (added {len(df) - before})")

    # Step 6: balance classes AND structure. Phishing rows are all kept. The
    # legitimate class is sampled to 1.5x phishing (60/40), separately for
    # bare domains and URLs with a path, so both classes have the same
    # bare/path mix and "has a path" carries no label information.
    df["has_path"] = df["url"].str.contains("/", regex=False)
    phish = df[df["label"] == 1]
    legit = df[df["label"] == 0]
    n_bare = int((~phish["has_path"]).sum() * 1.5)
    n_path = int(phish["has_path"].sum() * 1.5)
    legit_bare = legit[~legit["has_path"]]
    legit_path = legit[legit["has_path"]]
    if len(legit_bare) < n_bare or len(legit_path) < n_path:
        raise ValueError(
            f"Not enough legitimate rows: need {n_bare} bare / {n_path} path, "
            f"have {len(legit_bare)} / {len(legit_path)}"
        )
    before = len(df)
    df = pd.concat([
        legit_bare.sample(n=n_bare, random_state=42),
        legit_path.sample(n=n_path, random_state=42),
        phish,
    ])
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    print(f"[6] After balancing classes + structure to 60/40: {len(df)} rows (dropped {before - len(df)})")
    print("    Share of bare domains per class:")
    print(df.groupby("label")["has_path"].apply(lambda s: round(1 - s.mean(), 3)).to_string())

    return df[["url", "label"]]


def main():
    os.makedirs("data/processed", exist_ok=True)
    df = load_raw(RAW_PATH)
    tranco = load_tranco(TRANCO_PATH)
    cleaned = clean(df, tranco)
    cleaned.to_csv(OUT_PATH, index=False)

    print(f"\nSaved {len(cleaned)} rows to {OUT_PATH}")
    print("Class balance:")
    print(cleaned["label"].value_counts())


if __name__ == "__main__":
    main()