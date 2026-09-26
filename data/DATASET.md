# Dataset Documentation — Member 1

## Source
- **Name:** PhiUSIIL Phishing URL Dataset
- **URL:** https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset (downloaded via Kaggle mirror)
- **Licence:** CC BY 4.0
- **Date downloaded:** <2026-09-27>

## Raw data
- **Original row count:** 235795
- **Original columns:** 54 (URL, URLLength, Domain, DomainLength, IsDomainIP, TLD, ... label)
- **Original label values (before mapping):** 1 = legitimate, 0 = phishing

## Cleaning steps applied (via `ml/clean_data.py`)
1. Stripped leading/trailing whitespace from every URL
2. Dropped rows with empty URL or label
3. Dropped exact duplicate URLs
4. Mapped labels to integers: `legitimate → 0`, `phishing → 1` (inverted from raw, since raw dataset used the opposite convention)

- Rows before cleaning: 235795
- After stripping whitespace: 235795
- After dropping empty URL/label rows: 235795 (0 dropped)
- After dropping duplicate URLs: 235370 (425 dropped)
- After label mapping: 235370 (0 dropped)

## Class balance (after cleaning)
- Legitimate (0): 134850
- Phishing (1): 100520
- Ratio: ~57% legitimate / 43% phishing

## Train/test split
- Method: `train_test_split(..., stratify=y, random_state=42)`
- Split ratio: 80/20
- Train rows: (to be filled in after Phase 3 build)
- Test rows: (to be filled in after Phase 3 build)

## Notes
Switched from the classic UCI "Phishing Websites" dataset (id=327) to PhiUSIIL
because the original only contained pre-extracted numeric features with no
raw URL strings — unusable for a project that extracts its own features from
the URL text.