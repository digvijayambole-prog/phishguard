# PhishGuard API

One endpoint. The app analyses the URL **string only**: it never fetches, opens or
DNS-resolves the submitted address.

## POST /analyze

### Request

Send the URL as a form field or as JSON:

Input rules:

| Input | Result |
|---|---|
| empty or whitespace only | `E_EMPTY_URL` |
| `example.com` (no scheme) | normalised to `https://example.com`, accepted |
| `ftp://`, `file://`, `javascript:`, `data:` | `E_UNSUPPORTED_SCHEME` |
| longer than 2048 characters | `E_URL_TOO_LONG` |
| no parseable hostname, or an invalid port | `E_INVALID_URL` |
| control characters

Input rules:

| Input | Result |
|---|---|
| empty or whitespace only | `E_EMPTY_URL` |
| `example.com` (no scheme) | normalised to `https://example.com`, accepted |
| `ftp://`, `file://`, `javascript:`, `data:` | `E_UNSUPPORTED_SCHEME` |
| longer than 2048 characters | `E_URL_TOO_LONG` |
| no parseable hostname, or an invalid port | `E_INVALID_URL` |
| control characters (newline, carriage return, null, etc.) | `E_INVALID_URL` |
| contains `;` `\|` `&` `$` or a backtick, or any whitespace | `E_INVALID_URL` |
| valid URL with port, query or fragment | accepted |

### Response format

The `Accept` header decides the format. Browsers (which ask for HTML first) get the
HTML result or error page. curl, scripts and tests get JSON.

### Success response (200)

Example (values illustrative):

```json
{
  "url": "http://example.com/login",
  "prediction": "phishing",
  "risk_score": 68,
  "risk_level": "High",
  "indicators": [
    {
      "feature": "suspicious_keyword_count",
      "value": 1,
      "label": "Sensitive words in the address",
      "why": "Words like 'login', 'verify' or 'account' in an address are often associated with pages trying to look like real sign-in pages."
    }
  ],
  "explanation": "This address shows 1 characteristic commonly associated with phishing pages. The most notable: Sensitive words in the address.",
  "recommendation": "This address shows several characteristics commonly seen in phishing pages. Avoid entering passwords or payment information on this site.",
  "technical": {
    "features": { "url_length": 22, "hostname_length": 11 },
    "model": "RandomForestClassifier",
    "probability": 0.66
  }
}
```

| Field | Meaning |
|---|---|
| `prediction` | The model's label: `phishing` or `legitimate`. |
| `risk_score` | Integer 0-100. A **risk score, not a probability**: it has not been calibrated. |
| `risk_level` | `Low` (0-33), `Medium` (34-66) or `High` (67-100). Thresholds live only in `app/config.py`; clients should display this string, not recompute it. |
| `indicators` | Only the rules that actually triggered, most important first. May be empty. |
| `explanation` | One short paragraph built only from the triggered indicators. |
| `recommendation` | Fixed text for the risk level. |
| `technical` | Full feature values, model name and the model's phishing probability, for the technical view. |

`risk_score = round(100 * (0.70 * probability + 0.30 * rule_ratio))`, clamped to 0-100,
where `rule_ratio` is the fraction of the 7 rules that triggered.

`indicators` can be empty while the level is High. That means the model rates the
address as risky but no single clear warning sign could be pointed out. The
`explanation` says so plainly. The app never invents a reason.

### Error response

Every error uses this shape:

```json
{ "error": { "code": "E_INVALID_URL",
             "message": "Please enter a complete website URL.",
             "field": "url" } }
```

`field` is `"url"` for input errors and `null` otherwise.

| Code | HTTP | Message |
|---|---|---|
| `E_EMPTY_URL` | 400 | Please enter a website URL. |
| `E_INVALID_URL` | 400 | Please enter a complete website URL. |
| `E_UNSUPPORTED_SCHEME` | 400 | Only http and https addresses can be analysed. |
| `E_URL_TOO_LONG` | 400 | That URL is too long to analyse. |
| `E_MODEL_UNAVAILABLE` | 503 | Analysis is unavailable right now. Please try again later. |
| `E_FEATURE_FAILURE` | 500 | This URL could not be analysed. |
| `E_PREDICTION_INVALID` | 500 | This URL could not be analysed. |
| `E_EXPLANATION_FAILURE` | 500 | The analysis completed but could not be explained. |
| `E_INTERNAL` | 500 | Something went wrong. Please try again. |
| `E_RATE_LIMIT` | 429 | Too many requests. Please wait a minute and try again. |

The set is frozen at ten codes (`E_RATE_LIMIT` is returned with HTTP 429 above 10 requests per minute per client address). Unknown routes (404) and wrong methods (405) keep
their real HTTP status but use the `E_INTERNAL` body. No response ever contains a
stack trace or a file path.

`E_MODEL_UNAVAILABLE` is returned if the model file is missing, corrupt, or its feature
order does not match the schema. The model is loaded once at startup, and a mismatch
writes a critical log line at startup.
