import joblib, json
model = joblib.load("models/phishing_model.pkl")
schema = json.load(open("models/feature_schema.json"))
row = [[50,11,6,2,0,0,1,0,1,0,0,1]]
print(model.predict(row), model.predict_proba(row))