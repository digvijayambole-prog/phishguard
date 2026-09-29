## 4. Dataset & Feature Engineering

### 4.1 Dataset

**Sources:** the Kaggle "Malicious URLs Dataset" (651,191 URLs labeled
benign/phishing/defacement/malware) combined with the Tranco top-sites
list (top 500,000 ranked domains), used as a source of additional
legitimate bare domains.

We initially built the pipeline on the UCI PhiUSIIL Phishing URL Dataset,
but discovered a structural flaw during model evaluation: every legitimate
URL in it was a bare domain (no path), while phishing URLs typically had
one. A trained model exploited this shortcut rather than learning genuine
phishing indicators — e.g. it scored `github.com/user/repo` as 100%
phishing. We switched sources, only to find the Kaggle dataset had the
same flaw in reverse (just 103 legitimate bare domains out of ~140,000),
so we added Tranco specifically to supply real legitimate bare domains,
then balanced both **class size** (60% legitimate / 40% phishing) and
**URL structure** (23.3% bare domains in both classes) so neither factor
alone predicts the label.

**Cleaning** (`ml/clean_data.py`): stripped whitespace, removed the
`http(s)://` scheme and any leading `www.` (both were found to correlate
strongly with the label in the raw data and would otherwise leak into the
model), dropped duplicates and unmappable labels, merged in Tranco
domains, and balanced by class and structure with `random_state=42`.

**Result:** 232,872 rows — 139,723 legitimate, 93,149 phishing — split
80/20 (stratified, `random_state=42`) into 186,297 training and 46,575
test rows.

### 4.2 Feature Engineering

We designed 12 features (`ml/features.py`), computed directly from the
URL string with no network access: URL length, hostname length, path
length, punctuation counts (dots, hyphens, digits, special characters),
subdomain count, presence of HTTPS, presence of a bare IP host, presence
of an `@` symbol, and a count of 20 frozen suspicious keywords.

The function is pure and hardened to never raise an exception on any
input, including empty strings, malformed text, very long URLs, and
unicode domains, since it is called live on arbitrary user input by the
deployed web application.

**Distribution evidence** (means by class, training set):

| Feature | Mean (legitimate) | Mean (phishing) | Difference |
|---|---|---|---|
| `path_length` | 24.8 | 18.7 | 6.1 |
| `url_length` | 46.7 | 42.2 | 4.5 |
| `hostname_length` | 15.9 | 17.6 | 1.8 |
| `num_hyphens` | 1.45 | 0.47 | 0.98 |
| `num_digits` | 4.30 | 3.65 | 0.65 |

Two features show a large **relative** difference despite small absolute
values: `has_at_symbol` (0.09% of legitimate URLs vs 0.69% of phishing —
nearly 8x more common) and `has_ip_address` (0.005% vs 0.35% — roughly
65x more common), consistent with known phishing patterns even though
both are rare overall. `suspicious_keyword_count` was also nearly double
for phishing (0.16 vs 0.09).

Once the dataset's structural biases were removed, several features
reversed direction from an earlier (biased) analysis: legitimate URLs in
the corrected data are, on average, slightly *longer* and have longer
paths than phishing URLs, the opposite of the naive intuition that
phishing URLs are always longer. This reflects real crawled legitimate
pages (e.g. `espn.go.com/nba/player/_/id/3457/brandon-rush`) having
substantial paths, while several phishing entries are short, suspicious
bare domains.

**Known limitation:** `has_https` is constant 0 across this dataset,
because the URL scheme was deliberately stripped during cleaning (it was
found to leak label information — most raw phishing URLs had no scheme
at all, an artifact of how the data was collected, not a real signal).
`extract_features()` still computes this feature correctly for any live
URL the deployed model receives, but the trained model in this project
was not able to learn anything from it. Future work with a larger,
scheme-balanced dataset could recover this signal.
## 5. System Architecture

*(Member 3's section)*

## 6. Model Training & Evaluation

### 6.1 Methodology

Five candidate models were trained on the 186,297-row training set and
evaluated identically: Logistic Regression, Decision Tree, Random Forest,
XGBoost, and a small Multi-Layer Perceptron (MLP). Every model used the
same `random_state=42`, the same 12-feature input, and 5-fold
cross-validation scored on F1, since a naive accuracy metric is misleading
on a dataset where false phishing alerts on real sites carry a real cost.
The winning model was selected purely by cross-validation F1 (never by
peeking at the test set), then lightly tuned with a small grid search
(at most 2-3 values per hyperparameter) and evaluated once, finally, on
the held-out 46,575-row test set.

### 6.2 Results

| Model | Accuracy | Precision | Recall | F1 | CV F1 (mean ± std) |
|---|---|---|---|---|---|
| Logistic Regression | 0.6276 | 0.6256 | 0.1719 | 0.2697 | 0.2687 ± 0.0039 |
| Decision Tree | 0.7822 | 0.7501 | 0.6828 | 0.7149 | 0.7125 ± 0.0025 |
| **Random Forest** | **0.7981** | **0.7699** | **0.7064** | **0.7368** | **0.7365 ± 0.0012** |
| XGBoost | 0.7837 | 0.7588 | 0.6733 | 0.7135 | 0.7178 ± 0.0026 |
| MLP | 0.7646 | 0.7227 | 0.6677 | 0.6941 | 0.6882 ± 0.0136 |

Random Forest was selected as the winner: it had both the highest
cross-validation F1 and the tightest standard deviation (0.0012) of any
model, indicating the most stable performance across folds. Logistic
Regression's low recall (0.17) shows a simple linear model cannot capture
the interactions between these 12 URL-structure features.

After a light grid search (`n_estimators` ∈ {100, 200}, `max_depth` ∈
{10, 15}), the tuned Random Forest (`max_depth=15, n_estimators=100`)
scored **79.2% accuracy, 77.6% precision, 67.4% recall, 72.1% F1** on the
untouched test set — closely matching its cross-validation score, showing
no overfitting to the training data. The model was further constrained to
`max_leaf_nodes=5000` purely to reduce the exported file size from 49MB
to 12MB, at a cost of only 0.0012 in accuracy.

**Precision was treated as the priority metric**, since a false "phishing"
verdict on a legitimate site (e.g. a real bank) is the more expensive
error for this product's users than an occasional missed phishing site.

A note on the dataset: an earlier version of the feature matrix produced
suspiciously high accuracy (>99%) because legitimate and phishing URLs in
the source data differed structurally (all legitimate URLs were bare
domains) rather than by genuine phishing indicators. This was identified,
the dataset was corrected by mixing in the Tranco top-sites list and
re-balancing by URL structure, and all results above reflect the
corrected, unbiased data.