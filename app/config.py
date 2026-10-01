"""App settings. Risk thresholds live HERE and nowhere else."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = False
MAX_URL_LENGTH = 2048

RISK_THRESHOLDS = {"Low": (0, 33), "Medium": (34, 66), "High": (67, 100)}

MODEL_PATH = BASE_DIR / "models" / "phishing_model.pkl"
SCHEMA_PATH = BASE_DIR / "models" / "feature_schema.json"
IMPORTANCE_PATH = BASE_DIR / "models" / "feature_importance.json"
MAX_CONTENT_LENGTH = 16 * 1024
