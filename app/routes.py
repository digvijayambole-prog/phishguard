from flask import Blueprint, jsonify, request

from app import explainer, predictor, risk_engine
from app.errors import AppError
from app.validator import validate_url

bp = Blueprint("main", __name__)


@bp.route("/analyze", methods=["POST"])
def analyze():
    payload = request.get_json(silent=True) or {}
    raw = request.form.get("url") or payload.get("url")

    url = validate_url(raw)
    features = predictor.extract(url)
    label, probability = predictor.predict(features)

    score = risk_engine.calculate(probability, features)
    level = risk_engine.get_level(score)

    try:
        indicators = explainer.build_indicators(features)
        explanation = explainer.summarize(level, indicators)
        recommendation = explainer.RECOMMENDATIONS[level]
    except Exception:
        raise AppError("E_EXPLANATION_FAILURE")

    return jsonify({
        "url": url,
        "prediction": "phishing" if label == 1 else "legitimate",
        "risk_score": score,
        "risk_level": level,
        "indicators": indicators,
        "explanation": explanation,
        "recommendation": recommendation,
        "technical": {
            "features": features,
            "model": predictor.model.name,
            "probability": round(probability, 2),
        },
    })
