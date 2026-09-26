"""
Member 1 - Data & Features
Phase 3: Explore which features actually separate phishing from legitimate
URLs. Produces a correlation heatmap and distribution plots, saved as PNGs.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

TRAIN_PATH = "data/processed/train_features.csv"
FIGURES_DIR = "docs/figures"

FEATURE_COLUMNS = [
    "url_length", "hostname_length", "path_length", "num_dots",
    "num_hyphens", "num_digits", "num_special_chars", "num_subdomains",
    "has_https", "has_ip_address", "has_at_symbol", "suspicious_keyword_count",
]


def main():
    os.makedirs(FIGURES_DIR, exist_ok=True)
    df = pd.read_csv(TRAIN_PATH)
    print(f"Loaded {len(df)} rows")

    # --- 1. Which features separate the classes? Compare means. ---
    means_by_class = df.groupby("label")[FEATURE_COLUMNS].mean()
    print("\nFeature means by class (0=legit, 1=phishing):")
    print(means_by_class.T)

    # Rank features by absolute difference between class means
    diff = (means_by_class.loc[1] - means_by_class.loc[0]).abs().sort_values(ascending=False)
    print("\nTop 5 features by class separation (largest mean difference):")
    print(diff.head(5))

    # --- 2. Correlation heatmap (features + label) ---
    plt.figure(figsize=(10, 8))
    corr = df[FEATURE_COLUMNS + ["label"]].corr()
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0)
    plt.title("Feature Correlation Heatmap")
    plt.tight_layout()
    heatmap_path = os.path.join(FIGURES_DIR, "correlation_heatmap.png")
    plt.savefig(heatmap_path, dpi=150)
    plt.close()
    print(f"\nSaved {heatmap_path}")

    # --- 3. Distribution plots for the top 2 separating features ---
    top_features = diff.head(2).index.tolist()
    for feat in top_features:
        plt.figure(figsize=(8, 5))
        sns.histplot(data=df, x=feat, hue="label", bins=40, kde=True,
                     stat="density", common_norm=False,
                     palette={0: "steelblue", 1: "crimson"})
        plt.title(f"Distribution of {feat} by class (0=legit, 1=phishing)")
        plt.tight_layout()
        out_path = os.path.join(FIGURES_DIR, f"distribution_{feat}.png")
        plt.savefig(out_path, dpi=150)
        plt.close()
        print(f"Saved {out_path}")


if __name__ == "__main__":
    main()