# Model Comparison — Phishing URL Detection

Trained on 186,297 rows, tested on 46,575 rows (Kaggle Malicious URLs + Tranco, balanced 60/40).
Same split, same `random_state=42`, same metric code for every model.

| Model | Accuracy | Precision | Recall | F1 | CV F1 (mean ± std) |
|---|---|---|---|---|---|
| Logistic Regression | 0.6276 | 0.6256 | 0.1719 | 0.2697 | 0.2687 ± 0.0039 |
| Decision Tree | 0.7822 | 0.7501 | 0.6828 | 0.7149 | 0.7125 ± 0.0025 |
| **Random Forest (winner)** | **0.7981** | **0.7699** | **0.7064** | **0.7368** | **0.7365 ± 0.0012** |
| XGBoost | 0.7837 | 0.7588 | 0.6733 | 0.7135 | 0.7178 ± 0.0026 |
| MLP | 0.7646 | 0.7227 | 0.6677 | 0.6941 | 0.6882 ± 0.0136 |

**Tuned Random Forest (final, on test set):** accuracy 0.7918, precision 0.7763, recall 0.6737, F1 0.7214
(`max_depth=15, n_estimators=100, max_leaf_nodes=5000` — the leaf cap only trims file size, not accuracy).