# PhishGuard: AI-Based Phishing Website Detection

## 1. Introduction

Phishing websites impersonate trusted services to steal credentials, payment
details, or other sensitive information. PhishGuard is a web application that
takes a URL a user is unsure about and returns a risk score (0–100), a
Low/Medium/High risk level, and a plain-language explanation of what about
the address looks risky, without ever visiting, fetching, or resolving the
submitted site. The system combines a machine-learned classifier with a set
of human-verifiable rules, so that every score shown to a user is backed by
a reason they can check for themselves.

## 2. Problem Statement

Phishing remains one of the most common vectors for credential theft and
fraud, and attackers continually register new look-alike domains that
blacklist-based tools cannot catch until after the fact. A detection method
that works from the structure of the URL text alone — without needing to
visit the page, wait for a blacklist update, or depend on page content that
an attacker could manipulate — can give a user a warning before they ever
load a suspicious site. This project builds such a system: a classifier
trained on real phishing and legitimate URLs, wrapped in an interface that
explains its reasoning rather than returning a bare verdict.

## 3. Literature Review

Rule-based and blacklist-based phishing detection (e.g. Google Safe Browsing)
is accurate but reactive — a newly registered phishing domain is not caught
until it has already been reported and verified. This motivates
lexical/URL-based machine learning approaches, which classify a URL from
features of the string itself (length, structure, special characters)
without needing to visit the page or wait for a blacklist update, trading
some accuracy for speed and independence from external services. For the
legitimate-domain half of our data we used the Tranco list (Le Pochat et
al., *Tranco: A Research-Oriented Top Sites Ranking Hardened Against
Manipulation*, NDSS 2019), a ranking specifically designed to be stable and
resistant to manipulation for research use, in preference to ad hoc
"top sites" lists. This project's contribution is not a novel algorithm but
a carefully validated pipeline: every feature and every explanation rule
used was checked against the training data for genuine predictive lift
rather than assumed from intuition (see Sections 4 and 8), after an initial
dataset was found to contain a structural bias that a naive pipeline would
have missed entirely (Section 4.1).

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

PhishGuard is a Flask application built around one endpoint, `POST /analyze`.
A request passes through five stages, each in its own module:

1. **Validation** (`app/validator.py`): checks and normalises the submitted
   string.
2. **Feature extraction** (`app/predictor.py`, using `ml/features.py`):
   turns the URL into 12 numeric features.
3. **Prediction** (`app/predictor.py`): the Random Forest model returns a
   label and a phishing probability.
4. **Risk scoring** (`app/risk_engine.py`): blends the probability with a
   rule-based signal into a 0–100 score and maps it to Low, Medium or High.
5. **Explanation** (`app/explainer.py`): lists the rules that triggered, in
   plain English, with a summary and a recommendation.

The response is HTML for browsers (the result and error pages) and JSON for
API clients, chosen by the `Accept` header, so both use the same code path.
The model is loaded once at startup, not per request. Risk thresholds exist
in one place only, `app/config.py`, and the interface displays the
`risk_level` string it receives instead of recomputing it. The full API is
documented in `docs/API.md`.

### 5.1 Security Handling

Three absolute rules govern the backend: the app never fetches, opens, or
DNS-resolves the submitted URL, analysing the string only; the URL is never
passed to `os.system`, `subprocess`, `eval`, `exec`, or a file path (a
source search of `app/` for these calls returned nothing); and no stack
trace or filesystem path ever appears in a response, every error uses one
of ten fixed, frozen messages, verified by automated tests, with debug mode
off.

Input hardening rejects empty input, unsupported schemes (`ftp`, `file`,
`javascript`, `data`), URLs over 2,048 characters, missing hostnames,
invalid ports, control characters, and the characters `; | & $` and a
backtick. A scheme-less URL is normalised to `https://`.

Abuse protection limits `/analyze` to 10 requests per minute per client
address (`E_RATE_LIMIT`, HTTP 429, proxy-aware so a shared load-balancer IP
does not either lock out every visitor at once or fail to limit anyone),
caps request bodies at 16 KB, and attaches `X-Content-Type-Options`,
`X-Frame-Options`, `Referrer-Policy`, and a restrictive `Content-Security-
Policy` to every response.

Six failure boundaries were simulated against temporary copies of the model
files (the real files are never modified) and each returns the correct
error code with no stack trace: missing model file, corrupt model file,
and a reordered feature schema (all `E_MODEL_UNAVAILABLE`); an extractor
exception (`E_FEATURE_FAILURE`); invalid model output (`E_PREDICTION_
INVALID`); and an explainer exception (`E_EXPLANATION_FAILURE`).

A project-wide dependency audit (`pip-audit`) against the pinned
`requirements-app.txt`/`requirements-dev.txt` versions found no known
vulnerabilities. `.gitignore` excludes raw data, the virtual environment,
and any `.env` file; the one trained model file committed to the
repository (12 MB, under the project's 25 MB limit) was confirmed to
contain no other sensitive data.

**Known gaps:** the model file is loaded with `joblib` (pickle), so it must
come only from a trusted source — here, the project's own training
pipeline. There is no user authentication, since the tool has no accounts
or saved data to protect. Rate-limit counters are held in memory and reset
if the server restarts.

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
(at most 2–3 values per hyperparameter) and evaluated once, finally, on
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
`max_leaf_nodes=5000` purely to reduce the exported file size from 49 MB
to 12 MB, at a cost of only 0.0012 in accuracy.

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

## 7. Risk Scoring Methodology

Levels: Low 0–33, Medium 34–66, High 67–100.

**Why a blend.** The model supplies statistical evidence, and the rules
supply evidence a person can verify on screen. Blending means every
displayed score is connected to indicators the user can see.

**What the score is not.** It is a risk score, not a probability. The
model's output has not been calibrated, so the interface never says
"84% chance of phishing."

**Model performance, stated plainly.** On the held-out test set (46,575
rows) the Random Forest reached accuracy 0.79, precision 0.78, recall 0.67
and F1 0.72. Roughly one third of phishing URLs in the test set are
missed, and some legitimate addresses are flagged. For example,
`https://github.com/login` scored 56 (Medium) because of the word
"login" in its path. These are known limitations of a model that sees
only the URL string, and the 30% rule component does not fix them.

**Guards.** `calculate()` rejects a missing, non-numeric, NaN, or
out-of-range probability (`E_PREDICTION_INVALID`) and missing or null
feature values (`E_FEATURE_FAILURE`). Level mapping was tested at every
boundary: 32, 33, and 34; 66, 67, and 68; 0 and 100; and clamping of -5
and 105.

**Consistency with training.** The training data was cleaned by removing
the `http(s)://` scheme and a leading `www.` before feature extraction.
The predictor applies the same cleaning before extraction. `has_https`
was therefore constant (0) in training, and its importance in the feature
ranking is 0.0. For that reason the predictor gives the model 0 for that
feature, as in training, but reports the real value from the original URL
so the "no HTTPS" indicator never makes a false claim about an HTTPS site.

## 8. Explainability Approach

Each indicator comes from a rule with an explicit trigger condition, a
short label, and a one or two sentence `why`. The explainer lists only
rules that actually triggered. If it fails, the API returns
`E_EXPLANATION_FAILURE` instead of inventing a reason. The `why` texts
avoid technical words (feature, weight, classifier, probability, model)
and never claim certainty ("can be used to", "is often associated with").

**Rules were validated against the training data, not assumed.** We
measured how often each candidate rule triggers on phishing versus
legitimate URLs in the 186,297 training rows (74,519 phishing, 111,778
legitimate). "Lift" is the phishing trigger rate divided by the legitimate
trigger rate. A rule was kept only if its lift was at least 1.5 and it
covered at least 1% of phishing URLs.

| Rule kept | Threshold | Phishing % | Legitimate % | Lift |
|---|---|---|---|---|
| Several sub-domains | 2 or more | 6.2 | 2.4 | 2.5 |
| Long domain name | 27+ characters | 10.7 | 5.3 | 2.0 |
| Many dots | 3 or more | 22.6 | 11.9 | 1.9 |
| Sensitive words | 1 or more | 11.6 | 5.2 | 2.2 |
| Raw IP address | present | 0.4 | 0.0 | high, but rare |
| @ symbol | present | 0.7 | 0.1 | high, but rare |
| No HTTPS | absent | not testable | not testable | see below |

**Five candidate rules were removed** because the data contradicted them:
long URL, long path, many hyphens, many digits, and many special
characters. In this dataset legitimate URLs were more often long,
hyphenated, or symbol-heavy (lifts between 0.13 and 0.98 at the ordinary
thresholds, and no better than 1.39 even at extreme-tail thresholds).
Keeping these rules would have produced explanations that contradicted
the project's own data.

**Cost of that decision.** Path length is the model's most important
feature (permutation importance 0.118), but it cannot be shown to users
with an honest reason. When the score is High and no rule triggered, the
explanation says: *"The automated check rates this address as risky, but
no single clear warning sign can be pointed out."*

**The HTTPS rule** is kept as a standard security signal, but it cannot be
validated on this dataset because the scheme was removed from every
training row.

**Ranking.** Triggered indicators are ordered by permutation importance
(`feature_importance.json`). If that file is missing or invalid, a fixed
weight order is used, and the same set of indicators is returned either
way.

**Limits of these results.** The measurements describe this dataset
(Kaggle Malicious URLs plus Tranco top sites, balanced 60/40), not the
whole internet.

## 9. Implementation & UI

The interface follows a fixed information hierarchy on the result screen:
analysed URL, prediction, risk score (shown as "78 / 100", never a
percentage, to avoid implying false precision), risk level, key
indicators, plain-language explanation, safety recommendation, and a
collapsed "Technical details" panel for the full feature breakdown —
ordinary users see a clear verdict, and an evaluator can expand the
technical view for the full pipeline.

All colours are defined once as CSS custom properties (design tokens) and
consumed everywhere else, so there are no hardcoded colour values outside
the token definitions; this is enforced by an automated stylesheet test.
The interface supports both light and dark modes from the same token set,
and respects `prefers-reduced-motion` so any animation (e.g. the loading
state) is disabled for users who request it. Risk level is never
communicated by colour alone — every coloured badge also carries its text
label (Low/Medium/High) and an icon, verified by testing the interface in
greyscale. Every form input has a real `<label>`, every interactive element
has a visible focus ring, and the results region uses `aria-live="polite"`
so a screen reader announces the outcome. Text contrast was measured
programmatically and is enforced by automated tests requiring at least
4.5:1 for text and 3:1 for interactive controls, in both light and dark
mode.

User input is never trusted with Jinja2's `|safe` filter anywhere in the
templates, so Jinja2's default autoescaping applies to every
user-submitted value rendered on the page; this was verified by submitting
script-tag and event-handler XSS payloads into the URL field and
confirming they render as inert, visible text rather than executing.

A themed visual layer (shield iconography, colour-and-icon risk badges, a
reduced-motion-aware scan animation during loading) was added on top of
the accessibility-tested base styling without changing any token values
or failing any existing stylesheet test.

**[M4 to confirm/replace]:** exact count of UI-side automated tests, and
any additional accessibility findings from manual testing (320px width,
200% zoom, full keyboard-only navigation) not already covered above.

## 10. Testing & Results

The project's automated test suite covers the backend and the frontend
separately. The backend test suite includes URL validation across the 11
required cases (valid http/https, missing scheme, empty, whitespace-only,
malformed, invalid domain, with port, with query parameters, with
fragment, internationalised domain), security-input tests (quotes,
shell metacharacters, a 10,000-character string, percent-encoding,
unexpected schemes, control characters), route tests for the Flask app,
and the six simulated failure boundaries described in Section 5.1. The
frontend test suite (`tests/test_style.py`) independently verifies the
stylesheet: token-only colours, presence of both light and dark token
blocks, reduced-motion support, and contrast ratios at every required
colour pairing, in both themes — all 39 of these checks currently pass.

**[fill in before submission]:** exact combined pass count across the
full suite from the final merge (backend tests + frontend tests), and the
manual demo checklist results (clean-clone startup, valid/invalid URL
handling, all result fields visible, no stack trace anywhere, model loads
correctly, no secrets in the repo).

The system has also been exercised as a live deployment (Render), with
production-specific hardening validated there directly: debug mode
confirmed off, security headers present on real responses, and the rate
limiter confirmed to key off each visitor's real address rather than the
hosting platform's shared proxy address.

## 11. Conclusion & Future Scope

PhishGuard demonstrates that a URL-only phishing classifier, combined with
a transparent, data-validated rule layer, can give users an explainable
risk assessment without ever visiting the address in question. The
project's main technical finding was procedural as much as algorithmic:
two different public datasets each contained a structural artifact that
let a naive model "cheat" rather than learn genuine phishing signals, and
catching this required deliberately testing the trained model against
real, unbiased example URLs rather than trusting a high accuracy score at
face value. The same discipline was applied to the explanation rules,
five of which were removed because they were empirically contradicted by
the project's own training data rather than kept on assumption.

**Limitations:** the model sees only the URL string and not page content,
so it cannot detect a phishing page hosted at an otherwise-unremarkable
address, and it is only as representative as its training data (Kaggle
Malicious URLs plus Tranco), not the whole web. `has_https` currently
contributes no signal to the trained model due to a necessary dataset
correction (Section 4.2). The system has no user accounts and does not
persist analysis history between sessions.

**Future scope:** retraining with a larger, scheme-balanced dataset that
could recover an HTTPS signal without reintroducing the original bias;
incorporating domain age or WHOIS data as an additional (optional, opt-in)
signal, if a version of the project were extended beyond a purely
URL-string-only approach; calibrating the model's probability output so a
genuine confidence percentage could eventually be shown; and persisting
rate-limit state outside process memory if the deployment is scaled
beyond a single server instance.