from flask import Blueprint, jsonify, request

from app import predictor, risk_engine
from app.validator import validate_url

bp = Blueprint("main", __name__)

# TEMPORARY: moves to explainer.py in Phase 3.
RECOMMENDATIONS = {
    "Low": "No strong warning signs were found. Normal caution still applies "
           "- check the address bar before signing in anywhere.",
    "Medium": "Some characteristics of this address are unusual. Do not enter "
              "passwords or payment details unless you are certain the site is genuine.",
    "High": "This address shows several characteristics commonly seen in phishing "
            "pages. Avoid entering passwords or payment information on this site.",
}


@bp.route("/analyze", methods=["POST"])
def analyze():
    payload = request.get_json(silent=True) or {}
    raw = request.form.get("url") or payload.get("url")

    url = validate_url(raw)
    features = predictor.extract(url)
    label, probability = predictor.predict(features)

    score = risk_engine.calculate(probability, features)
    level = risk_engine.get_level(score)

    return jsonify({
        "url": url,
        "prediction": "phishing" if label == 1 else "legitimate",
        "risk_score": score,
        "risk_level": level,
        "indicators": [],  # TEMPORARY: filled by the explainer in Phase 3
        "explanation": "Detailed explanation is not available yet.",
        "recommendation": RECOMMENDATIONS[level],
        "technical": {
            "features": features,
            "model": predictor.model.name,
            "probability": round(probability, 2),
        },
    })
