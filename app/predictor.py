"""Feature extraction and prediction. Model is created ONCE at import time."""
from app.errors import AppError
from app.stubs import stub_extract_features, StubModel, FEATURE_ORDER  # swapped on Day 11

model = StubModel()


def extract(url):
    try:
        features = stub_extract_features(url)
        return {k: features[k] for k in FEATURE_ORDER}
    except Exception:
        raise AppError("E_FEATURE_FAILURE")


def predict(features):
    try:
        X = [[features[k] for k in FEATURE_ORDER]]
        label = int(model.predict(X)[0])
        probability = float(model.predict_proba(X)[0][1])
    except Exception:
        raise AppError("E_PREDICTION_INVALID")
    if label not in (0, 1) or not (0.0 <= probability <= 1.0):
        raise AppError("E_PREDICTION_INVALID")
    return label, probability
