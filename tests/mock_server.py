"""Serves the frozen response contract so the UI can be built before the real backend exists."""
import json
from pathlib import Path
from flask import Flask, request, render_template

ROOT = Path(__file__).resolve().parents[1]
app = Flask(app_name := __name__, template_folder=str(ROOT / "templates"), static_folder=str(ROOT / "static"))

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    url = request.form.get("url", "")
    if not url.strip():
        data = json.loads((ROOT / "fixtures" / "error_empty.json").read_text(encoding="utf-8"))
        return render_template("error.html", **data), 400

    # Change this filename to preview another UI state.
    data = json.loads((ROOT / "fixtures" / "result_high.json").read_text(encoding="utf-8"))
    data["url"] = url
    return render_template("result.html", **data)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
