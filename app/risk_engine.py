"""Risk engine. Thresholds are read from config only."""
from app import config


def get_level(score):
    score = max(0, min(100, int(score)))
    for level, (low, high) in config.RISK_THRESHOLDS.items():
        if low <= score <= high:
            return level
    return "High"
