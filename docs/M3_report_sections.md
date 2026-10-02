# Member 3 report sections: Backend and Analysis Engine

Paste these into `docs/REPORT.md` (Member 1 owns that file). Every number below was measured on the project's own data or read from the project's own files. Items marked **[fill in]** are things not measured yet.

---

## Architecture

PhishGuard is a Flask application built around one endpoint, `POST /analyze`. A request passes through five stages, each in its own module:

1. **Validation** (`app/validator.py`): checks and normalises the submitted string.
2. **Feature extraction** (`app/predictor.py`, using Member 1's `ml/features.py`): turns the URL into 12 numeric features.
3. **Prediction** (`app/predictor.py`): Member 2's Random Forest returns a label and a phishing probability.
4. **Risk scoring** (`app/risk_engine.py`): blends the probability with a rule-based signal into a 0 to 100 score and maps it to Low, Medium or High.
5. **Explanation** (`app/explainer.py`): lists the rules that triggered, in plain English, with a summary and a recommendation.

The response is HTML for browsers (Member 4's result and error pages) and JSON for API clients, chosen by the `Accept` header, so both use the same code path. The model is loaded once at startup, not per request. Risk thresholds exist in one place only, `app/config.py`, and the interface displays the `risk_level` string it receives instead of recomputing it. The API is documented in `docs/API.md`.

---

## Risk Scoring Methodology

```
rule_ratio = triggered_rules / 7
score      = round(100 * (0.70 * probability + 0.30 * rule_ratio)), clamped to 0..100
```

Levels: Low 0 to 33, Medium 34 to 66, High 67 to 100.

**Why a blend.** The model supplies statistical evidence, and the rules supply evidence a person can verify on screen. Blending means every displayed score is connected to indicators the user can see.

**What the score is not.** It is a risk score, not a probability. The model's output has not been calibrated, so the interface never says "84% chance of phishing."

**Model performance, stated plainly.** On the held-out test set (46,575 rows) the Random Forest reached accuracy 0.79, precision 0.78, recall 0.67 and F1 0.72. Roughly one third of phishing URLs in the test set are missed, and some legitimate addresses are flagged. For example, `https://github.com/login` scored 56 (Medium) because of the word "login" in its path. These are known limitations of a model that sees only the URL string, and the 30% rule component does not fix them.

**Guards.** `calculate()` rejects a missing, non-numeric, NaN or out-of-range probability (`E_PREDICTION_INVALID`) and missing or null feature values (`E_FEATURE_FAILURE`). Level mapping was tested at every boundary: 32, 33 and 34; 66, 67 and 68; 0 and 100; and clamping of -5 and 105.

**Consistency with training.** The training data was cleaned by removing the `http(s)://` scheme and a leading `www.` before feature extraction. The predictor applies the same cleaning before extraction. `has_https` was therefore constant (0) in training, and its importance in Member 2's ranking is 0.0. For that reason the predictor gives the model 0 for that feature, as in training, but reports the real value from the original URL so the "no HTTPS" indicator never makes a false claim about an HTTPS site.

---

## Explainability Approach

Each indicator comes from a rule with an explicit trigger condition, a short label and a one or two sentence `why`. The explainer lists only rules that actually triggered. If it fails, the API returns `E_EXPLANATION_FAILURE` instead of inventing a reason. The `why` texts avoid technical words (feature, weight, classifier, probability, model) and never claim certainty ("can be used to", "is often associated with").

**Rules were validated against the training data, not assumed.** We measured how often each candidate rule triggers on phishing versus legitimate URLs in the 186,297 training rows (74,519 phishing, 111,778 legitimate). "Lift" is the phishing trigger rate divided by the legitimate trigger rate. A rule was kept only if its lift was at least 1.5 and it covered at least 1% of phishing URLs.

| Rule kept | Threshold | Phishing % | Legitimate % | Lift |
|---|---|---|---|---|
| Several sub-domains | 2 or more | 6.2 | 2.4 | 2.5 |
| Long domain name | 27 or more characters | 10.7 | 5.3 | 2.0 |
| Many dots | 3 or more | 22.6 | 11.9 | 1.9 |
| Sensitive words | 1 or more | 11.6 | 5.2 | 2.2 |
| Raw IP address | present | 0.4 | 0.0 | high, but rare |
| @ symbol | present | 0.7 | 0.1 | high, but rare |
| No HTTPS | absent | not testable | not testable | see below |

**Five candidate rules were removed** because the data contradicted them: long URL, long path, many hyphens, many digits and many special characters. In this dataset legitimate URLs were more often long, hyphenated or symbol-heavy (lifts between 0.13 and 0.98 at the ordinary thresholds, and no better than 1.39 even at extreme-tail thresholds). We tested the extreme tails as a possible rescue and none passed. Keeping these rules would have produced explanations that contradicted the project's own data.

**Cost of that decision.** Path length is the model's most important feature (permutation importance 0.118), but it cannot be shown to users with an honest reason. When the score is High and no rule triggered, the explanation says: "The automated check rates this address as risky, but no single clear warning sign can be pointed out."

**The HTTPS rule** is kept as a standard security signal, but it cannot be validated on this dataset because the scheme was removed from every training row.

**Ranking.** Triggered indicators are ordered by Member 2's `feature_importance.json` (permutation importance). If that file is missing or invalid, a fixed weight order is used, and the same set of indicators is returned either way.

**Limits of these results.** The measurements describe this dataset (Kaggle Malicious URLs plus Tranco top sites, balanced 60/40), not the whole internet.

---

## Security Handling

**Three absolute rules:**

1. The app never fetches, opens or DNS-resolves the submitted URL. It analyses the string only.
2. The URL is never passed to `os.system`, `subprocess`, `eval`, `exec` or a file path. A source search of `app/` for network, subprocess, `eval` and `exec` calls returned nothing.
3. No stack trace or filesystem path appears in a response body. Every error uses the frozen JSON shape with one of ten fixed messages, and 404 and 405 responses use the same shape. Automated tests check error responses for tracebacks and paths. Debug mode is off.

**Input hardening.** Empty input, unsupported schemes (ftp, file, javascript, data), URLs over 2,048 characters, missing hostnames, invalid ports, control characters and the characters `; | & $` and backtick are all rejected with specific error codes. A URL without a scheme is normalised to `https://`.

**Abuse protection.** `/analyze` accepts at most 10 requests per minute per client address (`E_RATE_LIMIT`, HTTP 429), request bodies are capped at 16 KB, and every response carries `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` and a restrictive `Content-Security-Policy` that forbids inline styles and scripts. Behind a hosting proxy the limiter reads the client address only when the deployment explicitly trusts one proxy hop.

**Failure handling.** Six failure boundaries were simulated and each returns the correct code without a stack trace: missing model file, corrupt model file and reordered feature schema (all `E_MODEL_UNAVAILABLE`, the last with a critical startup log line); extractor exception (`E_FEATURE_FAILURE`); invalid model output (`E_PREDICTION_INVALID`); explainer exception (`E_EXPLANATION_FAILURE`). The simulations use temporary copies of the model files, so the real files are never modified.

**Testing.** 61 backend tests and Member 4's 27 tests pass. **[fill in]** the final combined count after the last merge.

**Known gaps.** The model file is loaded with `joblib` (pickle), so it must come only from a trusted source, which here is Member 2. There is no authentication, and rate-limit counters are held in memory, so they reset when the server restarts. **[fill in]** response time measurements if the marking scheme asks for them.
