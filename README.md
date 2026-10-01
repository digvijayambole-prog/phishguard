# PhishGuard

AI-based phishing website detection with explainable risk analysis.

Paste a web address and PhishGuard returns a risk score out of 100, a Low / Medium / High
level, and plain-English reasons for the result. It analyses the address string only: it
**never visits, opens or resolves the submitted URL**.

## How it works

1. The URL is validated and normalised (`app/validator.py`).
2. 12 numeric features are extracted from the address string (`ml/features.py`).
3. A Random Forest model returns a phishing probability (`models/phishing_model.pkl`).
4. A risk score blends the model (70%) with human-checkable rules (30%) (`app/risk_engine.py`).
5. Every rule that triggered is explained in plain language (`app/explainer.py`).

The score is a risk score, not a calibrated probability.

## Install

Requires Python 3.10 or newer (developed on Python 3.13).

```bash
git clone https://github.com/digvijayambole-prog/phishguard.git
cd phishguard
python -m venv venv
```

Activate the environment:

- Git Bash on Windows: `source venv/Scripts/activate`
- Windows PowerShell: `venv\Scripts\Activate.ps1`
- macOS / Linux: `source venv/bin/activate`

```bash
pip install -r requirements-app.txt
```

## Run

```bash
flask --app app run
```

Open http://127.0.0.1:5000 in your browser.

The trained model is included in the repository, so nothing else needs to be downloaded.

## Try it from the command line

```bash
curl -X POST http://127.0.0.1:5000/analyze -d "url=https://example.com"
```

Browsers get the web page; curl and scripts get JSON. The full request, response and error
reference is in [docs/API.md](docs/API.md).

## Tests

```bash
python -m pytest tests -q
```

## Project layout

| Folder | Contents |
|---|---|
| `app/` | Flask application: validation, prediction, risk score, explanations |
| `templates/`, `static/` | The web interface |
| `ml/`, `data/`, `models/` | Feature extraction, dataset preparation, model training and the trained model |
| `tests/`, `fixtures/` | Automated tests and sample responses |
| `docs/` | API reference and report material |

## Known limitations

- On the held-out test set the model reaches about 79% accuracy and 67% recall, so some
  phishing addresses are missed and some genuine ones are flagged. It looks at the address
  string only, never at page content.
- The explanation rules were checked against the training data, and rules the data
  contradicted were removed. Results describe that dataset (Kaggle Malicious URLs plus
  Tranco top sites), not the whole internet.
- Treat the result as a warning sign, not a verdict.
