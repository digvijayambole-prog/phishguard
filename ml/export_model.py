"""
Member 2 - Phase 4: export the winning model + the three JSON artifacts.
"""
import json
import joblib
import pandas as pd
from datetime import date
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance

FEATURE_ORDER = [
    "url_length", "hostname_length", "path_length", "num_dots",
    "num_hyphens", "num_digits", "num_special_chars", "num_subdomains",
    "has_https", "has_ip_address", "has_at_symbol", "suspicious_keyword_count",
]

train = pd.read_csv("data/processed/train_features.csv")
test = pd.read_csv("data/processed/test_features.csv")
X_train, y_train = train[FEATURE_ORDER], train["label"]
X_test, y_test = test[FEATURE_ORDER], test["label"]

model = RandomForestClassifier(
    n_estimators=100, max_depth=15, max_leaf_nodes=5000,
    random_state=42, n_jobs=-1
)
model.fit(X_train, y_train)

joblib.dump(model, "models/phishing_model.pkl", compress=3)
print("Saved models/phishing_model.pkl")

result = permutation_importance(model, X_test, y_test, n_repeats=10, random_state=42, n_jobs=-1)
importances = {f: float(round(v, 4)) for f, v in zip(FEATURE_ORDER, result.importances_mean)}
with open("models/feature_importance.json", "w") as f:
    json.dump({"model": "RandomForestClassifier", "method": "permutation_importance",
               "importances": importances}, f, indent=2)
print("Saved models/feature_importance.json")

pred = model.predict(X_test)
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
metrics = {
    "accuracy": round(float(accuracy_score(y_test, pred)), 4),
    "precision": round(float(precision_score(y_test, pred)), 4),
    "recall": round(float(recall_score(y_test, pred)), 4),
    "f1": round(float(f1_score(y_test, pred)), 4),
}
card = {
    "algorithm": "RandomForestClassifier",
    "hyperparameters": {"n_estimators": 100, "max_depth": 15},
    "random_seed": 42,
    "dataset": "Kaggle Malicious URLs + Tranco top sites",
    "train_rows": len(train), "test_rows": len(test),
    "metrics": metrics,
    "trained_on": str(date.today()),
    "feature_schema_version": "1.0",
}
with open("models/model_card.json", "w") as f:
    json.dump(card, f, indent=2)
print("Saved models/model_card.json:", card)