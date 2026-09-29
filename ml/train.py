import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

train = pd.read_csv("data/processed/train_features.csv")
test = pd.read_csv("data/processed/test_features.csv")
X_train, y_train = train.drop(columns="label"), train["label"]
X_test, y_test = test.drop(columns="label"), test["label"]

models = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
}

for name, model in models.items():
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    print(f"{name}: accuracy={accuracy_score(y_test, pred):.4f} "
          f"precision={precision_score(y_test, pred):.4f} "
          f"recall={recall_score(y_test, pred):.4f} "
          f"f1={f1_score(y_test, pred):.4f}")