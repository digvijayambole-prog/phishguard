"""
Member 2 - Model Training & Evaluation
Trains 5 models, compares them with 5-fold CV, tunes the winner,
and reports final test-set metrics. Same split/seed for every model.
"""

import pandas as pd
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from xgboost import XGBClassifier

from ml.evaluate import compute_metrics, save_confusion_matrix, save_roc_curve

TRAIN_PATH = "data/processed/train_features.csv"
TEST_PATH = "data/processed/test_features.csv"
SEED = 42

train = pd.read_csv(TRAIN_PATH)
test = pd.read_csv(TEST_PATH)
X_train, y_train = train.drop(columns="label"), train["label"]
X_test, y_test = test.drop(columns="label"), test["label"]

models = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=SEED),
    "Decision Tree": DecisionTreeClassifier(random_state=SEED),
    "Random Forest": RandomForestClassifier(n_estimators=200, random_state=SEED, n_jobs=-1),
    "XGBoost": XGBClassifier(random_state=SEED, eval_metric="logloss"),
    "MLP": MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=500, random_state=SEED),
}

print("=" * 70)
print("PHASE 2: 5-fold cross-validation (F1) + held-out test metrics")
print("=" * 70)

results = []
fitted = {}
for name, model in models.items():
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="f1", n_jobs=-1)
    model.fit(X_train, y_train)
    fitted[name] = model
    pred = model.predict(X_test)
    m = compute_metrics(y_test, pred)
    m["cv_f1_mean"] = cv_scores.mean()
    m["cv_f1_std"] = cv_scores.std()
    m["model"] = name
    results.append(m)
    print(f"{name:22s} acc={m['accuracy']:.4f} prec={m['precision']:.4f} "
          f"rec={m['recall']:.4f} f1={m['f1']:.4f} "
          f"cv_f1={m['cv_f1_mean']:.4f}+/-{m['cv_f1_std']:.4f}")

results_df = pd.DataFrame(results).set_index("model")
results_df.to_csv("docs/model_comparison_raw.csv")

winner_name = results_df["cv_f1_mean"].idxmax()
print(f"\nWinner by CV F1: {winner_name}")

print("=" * 70)
print(f"PHASE 2.5: light tuning of the winner ({winner_name})")
print("=" * 70)

param_grids = {
   "Random Forest": {"n_estimators": [100, 200], "max_depth": [10, 15]},
    "XGBoost": {"n_estimators": [100, 200, 300], "max_depth": [4, 6, 8]},
    "Decision Tree": {"max_depth": [8, 12, None]},
    "Logistic Regression": {"C": [0.1, 1.0, 10.0]},
    "MLP": {"hidden_layer_sizes": [(32,), (32, 16), (64, 32)]},
}

if winner_name in param_grids:
    grid = GridSearchCV(models[winner_name], param_grids[winner_name], cv=5, scoring="f1", n_jobs=-1, verbose=2)
    grid.fit(X_train, y_train)
    print(f"Best params: {grid.best_params_}")
    final_model = grid.best_estimator_
else:
    final_model = fitted[winner_name]

final_pred = final_model.predict(X_test)
final_metrics = compute_metrics(y_test, final_pred)
print(f"\nFinal tuned {winner_name} on test set: {final_metrics}")

print("=" * 70)
print("Saving figures")
print("=" * 70)
save_confusion_matrix(y_test, final_pred, winner_name, f"docs/figures/confusion_matrix_{winner_name.replace(' ', '_')}.png")
save_roc_curve(final_model, X_test, y_test, winner_name, f"docs/figures/roc_curve_{winner_name.replace(' ', '_')}.png")

print("\nComparison table saved to docs/model_comparison_raw.csv")
print("Done. Next: export the winner as models/phishing_model.pkl (Phase 4).")