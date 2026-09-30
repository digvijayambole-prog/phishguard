"""Feature extraction and prediction using M1's extractor and M2's model.
The model is loaded ONCE at import time, never inside the route."""
import json
import logging
import re
import warnings

import joblib

from app import config
from app.errors import AppError
from ml.features import extract_features, FEATURE_ORDER

log = logging.getLogger("phishguard.predictor")
warnings.filterwarnings("ignore", message="X does not have valid feature names")

MODEL_NAME = "RandomForestClassifier"

# Training URLs had the scheme and a leading "www." removed (ml/clean_data.py, steps 2b/2c).
_SCHEME_RE = re.compile(r"^https?://", re.IGNORECASE)
_WWW_RE = re.compile(r"^www\.", re.IGNORECASE)


def _load_model():
    try:
        with open(config.SCHEMA_PATH, encoding="utf-8") as fh:
            schema = json.load(fh)
        if schema["feature_order"] != FEATURE_ORDER:
            log.critical("FEATURE ORDER MISMATCH between feature_schema.json and "
                         "ml.features - model disabled")
            return None
        loaded = joblib.load(config.MODEL_PATH)
        if list(loaded.classes_) != [0, 1] or loaded.n_features_in_ != len(FEATURE_ORDER):
            log.critical("Model classes or feature count do not match the contract "
                         "- model disabled")
            return None
        return loaded
    except Exception:
        log.critical("Model could not be loaded - /analyze will return "
                     "E_MODEL_UNAVAILABLE", exc_info=True)
        return None


model = _load_model()


def normalise_for_model(url):
    """Apply the same cleaning that produced the training data."""
    return _WWW_RE.sub("", _SCHEME_RE.sub("", url.strip()))


def extract(url):
    try:
        raw = extract_features(normalise_for_model(url))
        features = {k: int(raw[k]) for k in FEATURE_ORDER}
        # Report the REAL scheme so the HTTPS rule never makes a false claim.
        features["has_https"] = 1 if url.strip().lower().startswith("https://") else 0
        return features
    except Exception:
        raise AppError("E_FEATURE_FAILURE")


def predict(features):
    if model is None:
        raise AppError("E_MODEL_UNAVAILABLE")
    try:
        row = [features[k] for k in FEATURE_ORDER]
        # has_https was constant 0 in training (scheme stripped), so pass 0 to match it.
        row[FEATURE_ORDER.index("has_https")] = 0
        X = [row]
        label = int(model.predict(X)[0])
        probability = float(model.predict_proba(X)[0][1])
    except Exception:
        raise AppError("E_PREDICTION_INVALID")
    if label not in (0, 1) or not (0.0 <= probability <= 1.0):
        raise AppError("E_PREDICTION_INVALID")
    return label, probability
