"""Risk engine: blends model evidence with human-verifiable rules into a 0-100 score.
Thresholds are read from config only."""
import math

from app import config
from app.errors import AppError
from app.explainer import RULES, TOTAL_RULES


def _check_probability(probability):
    if (isinstance(probability, bool) or not isinstance(probability, (int, float))
            or math.isnan(probability) or not (0.0 <= probability <= 1.0)):
        raise AppError("E_PREDICTION_INVALID")


def count_triggered(features):
    if not isinstance(features, dict):
        raise AppError("E_FEATURE_FAILURE")
    triggered = 0
    for rule in RULES:
        value = features.get(rule["feature"])
        if value is None or (isinstance(value, float) and math.isnan(value)):
            raise AppError("E_FEATURE_FAILURE")
        if rule["triggers_when"](value):
            triggered += 1
    return triggered


def calculate(probability, features):
    _check_probability(probability)
    rule_ratio = count_triggered(features) / TOTAL_RULES
    score = round(100 * (0.70 * probability + 0.30 * rule_ratio))
    return max(0, min(100, score))


def get_level(score):
    score = max(0, min(100, round(score)))
    for level, (low, high) in config.RISK_THRESHOLDS.items():
        if low <= score <= high:
            return level
    return "High"
