## 4. Dataset & Feature Engineering

### 4.1 Dataset

**Source:** PhiUSIIL Phishing URL Dataset (Prasad & Chandra, 2024), obtained
via its UCI Machine Learning Repository listing and downloaded through a
Kaggle mirror. Licensed under CC BY 4.0.

We initially considered the older UCI "Phishing Websites" dataset, but it
contains only pre-extracted numeric features with no raw URL strings —
unusable for a project whose core requirement is extracting features
directly from URL text. PhiUSIIL was chosen instead: it provides 235,795
real URLs labeled as legitimate or phishing, collected from live web
sources.

**Cleaning process** (`ml/clean_data.py`):
1. Stripped leading/trailing whitespace from every URL
2. Dropped rows with an empty URL or label (0 rows affected)
3. Dropped exact duplicate URLs (425 rows removed)
4. Mapped labels to integers — the raw dataset uses `1 = legitimate,
   0 = phishing`, which we inverted to our project's convention of
   `0 = legitimate, 1 = phishing`

**Result:** 235,370 cleaned rows.
- Legitimate (0): 134,850
- Phishing (1): 100,520
- Class balance: ~57% / 43% — well within an acceptable range for
  classification without needing resampling.

**Split:** stratified 80/20 train/test split (`random_state=42`), giving
188,296 training rows and 47,074 test rows, each preserving the original
class ratio.

### 4.2 Feature Engineering

We designed 12 features (`ml/features.py`), each computed directly from the
URL string with no network access, chosen to capture patterns known to
correlate with phishing attempts: URL length, hostname length, path length,
punctuation counts (dots, hyphens, digits, special characters), subdomain
count, presence of HTTPS, presence of a bare IP address as the host,
presence of an `@` symbol, and a count of 20 frozen suspicious keywords
(e.g. "login", "verify", "secure", "paypal") appearing in the URL.

The function is pure and defensively hardened to never raise an exception
regardless of input — including empty strings, malformed text, extremely
long URLs, and internationalized (unicode) domains — since it is called
live on arbitrary user input in the deployed web application.

**Distribution evidence:** comparing feature means between the two classes
across our training set showed a clear separation on several features
(see `docs/figures/correlation_heatmap.png` and the accompanying
distribution plots):

| Feature | Mean (legitimate) | Mean (phishing) | Difference |
|---|---|---|---|
| `url_length` | 27.2 | 46.4 | **19.1** |
| `path_length` | 0.0 | 8.7 | **8.7** |
| `hostname_length` | 19.2 | 24.5 | **5.2** |
| `num_digits` | 0.05 | 4.4 | **4.3** |
| `num_hyphens` | 0.08 | 0.71 | 0.6 |

`url_length` was the single strongest separator: phishing URLs average
nearly double the length of legitimate ones, consistent with attackers
padding URLs with deceptive subdomains and path segments to imitate
trusted brands (e.g. `secure-login-verify.paypal.com.attacker.ru`). Legit
URLs in this dataset were overwhelmingly bare domains (`path_length` of
0), while phishing URLs consistently included extra path segments.
`has_https` also showed a strong categorical split (100% of legitimate
URLs vs. 49% of phishing URLs used HTTPS), though as a binary feature it
is not directly comparable in magnitude to the length-based features
above.