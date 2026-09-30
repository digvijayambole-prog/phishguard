from flask import Blueprint, jsonify

bp = Blueprint("main", __name__)


@bp.route("/analyze", methods=["POST"])
def analyze():
    # HARDCODED placeholder: real validation, scoring and explanation come later.
    return jsonify({
        "url": "https://example.com/login",
        "prediction": "phishing",
        "risk_score": 78,
        "risk_level": "High",
        "indicators": [
            {
                "feature": "url_length",
                "value": 142,
                "label": "Unusually long URL",
                "why": "Very long web addresses can be used to push the real "
                       "destination out of sight in the address bar.",
            }
        ],
        "explanation": "This address shows characteristics commonly associated with phishing pages.",
        "recommendation": "Avoid entering passwords or payment information on this site.",
        "technical": {
            "features": {"url_length": 142},
            "model": "RandomForestClassifier",
            "probability": 0.84,
        },
    })
