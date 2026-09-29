# Dataset Documentation — Member 1

## Sources
1. **Kaggle "Malicious URLs Dataset"** (`malicious_phish.csv`) — 651,191 URLs
   labeled `benign`, `phishing`, `defacement`, or `malware`. Only `benign`
   and `phishing` rows were kept.
2. **Tranco top-sites list** (`tranco.csv`, tranco-list.eu) — top 500,000
   ranked domains, added as extra legitimate bare domains. Citation:
   Le Pochat et al., *Tranco: A Research-Oriented Top Sites Ranking
   Hardened Against Manipulation*, NDSS 2019.
- **Licence:** Kaggle dataset — public domain / CC0 (per Kaggle listing).
  Tranco — free for research use.
- **Date downloaded:** 2026-09-28

## Why two sources
An initial dataset (PhiUSIIL, UCI) was used and abandoned after we found
every legitimate URL in it was a bare domain (no path), while phishing
URLs mostly had paths. A model trained on it learned "has a path = phishing"
rather than any real signal — e.g. `github.com/user/repo` scored 1.00
phishing probability. We switched to the Kaggle dataset, but it had the
same flaw in reverse (99.5% of bare domains in it were phishing, since it
had almost no legitimate bare domains — only 103). Tranco was added purely
to give the model real legitimate bare domains.

## Cleaning steps applied (via `ml/clean_data.py`)
1. Strip whitespace from every URL
2. Remove the `http(s)://` scheme — a collection artifact (92% of legit
   URLs in the raw file had none, vs 26% of phishing)
3. Remove a leading `www.` — same reason (39% of phishing vs 3% of legit)
4. Drop empty URL/label rows
5. Drop exact duplicate URLs (15,965 dropped)
6. Map labels: `benign → 0`, `phishing → 1`; drop `defacement`/`malware`
   rows (118,901 dropped)
7. Merge in Tranco domains as additional legitimate (label 0) rows,
   de-duplicated against the existing set
8. Balance both class size (60% legit / 40% phishing) **and URL structure**
   (23.3% bare domains in both classes), by random sampling with
   `random_state=42`, so "has a path" carries no information about the label

## Result
- **Total cleaned rows:** 232,872
- **Legitimate (0):** 139,723
- **Phishing (1):** 93,149
- **Class balance:** ~60% / 40%
- **Bare-domain share:** 23.3% in both classes (structurally balanced)

## Train/test split
- Method: `train_test_split(..., stratify=y, random_state=42)`
- Split ratio: 80/20
- Train rows: 186,297
- Test rows: 46,575

## Notes
`has_https` is constant 0 across the entire dataset by construction (the
scheme was stripped during cleaning to remove bias), so it carries no
signal in this project's trained model, even though `extract_features()`
still computes it correctly for any live URL. This is disclosed as a
known limitation in the report.