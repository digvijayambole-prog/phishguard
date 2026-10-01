# Team contracts

Agreed on Day 0. Never change these alone: tell everyone first.

## The 12 features (in this exact order)

`url_length`, `hostname_length`, `path_length`, `num_dots`, `num_hyphens`, `num_digits`,
`num_special_chars`, `num_subdomains`, `has_https`, `has_ip_address`, `has_at_symbol`,
`suspicious_keyword_count`

All numeric. The `has_*` features are 0 or 1. The order is stored in
`models/feature_schema.json` and the app refuses to use the model if it does not match
`ml/features.py`.

Training URLs had `http(s)://` and a leading `www.` removed before feature extraction, so
the app applies the same cleaning before prediction.

## Model

`models/phishing_model.pkl`, loaded once at startup. Label `0` = legitimate, `1` = phishing.
The phishing probability is `predict_proba(X)[0][1]`, a float from 0.0 to 1.0.

## Suspicious keywords (frozen)

login, log-in, signin, sign-in, verify, verification, secure, security, account, update,
confirm, banking, bank, password, credential, webscr, paypal, invoice, billing, recover

## Risk score and levels

```
score = round(100 * (0.70 * probability + 0.30 * rule_ratio)), clamped to 0..100
```

| Level | Score |
|---|---|
| Low | 0 to 33 |
| Medium | 34 to 66 |
| High | 67 to 100 |

Thresholds live only in `app/config.py`. The interface displays the `risk_level` string it
receives and never recomputes it.

## Success response

`url`, `prediction` ("phishing" or "legitimate"), `risk_score` (integer 0 to 100),
`risk_level`, `indicators` (list of `feature`, `value`, `label`, `why`), `explanation`,
`recommendation`, and `technical` (`features`, `model`, `probability`).
Full example in [docs/API.md](docs/API.md).

## Error response

`{ "error": { "code": ..., "message": ..., "field": ... } }`

Ten codes. E_RATE_LIMIT was added with team-lead approval; no further additions. Always show the message exactly as sent.

| Code | HTTP | Message |
|---|---|---|
| E_EMPTY_URL | 400 | Please enter a website URL. |
| E_INVALID_URL | 400 | Please enter a complete website URL. |
| E_UNSUPPORTED_SCHEME | 400 | Only http and https addresses can be analysed. |
| E_URL_TOO_LONG | 400 | That URL is too long to analyse. |
| E_MODEL_UNAVAILABLE | 503 | Analysis is unavailable right now. Please try again later. |
| E_FEATURE_FAILURE | 500 | This URL could not be analysed. |
| E_PREDICTION_INVALID | 500 | This URL could not be analysed. |
| E_EXPLANATION_FAILURE | 500 | The analysis completed but could not be explained. |
| E_INTERNAL | 500 | Something went wrong. Please try again. |
| E_RATE_LIMIT | 429 | Too many requests. Please wait a minute and try again. |

## Security rules

1. The app never fetches, opens or DNS-resolves a submitted URL. It analyses the string only.
2. A submitted URL is never passed to a shell, `eval`, or a file path.
3. No stack trace or file path ever appears in a response.
