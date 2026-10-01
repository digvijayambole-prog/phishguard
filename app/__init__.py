from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, app=app, default_limits=[])
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from app.errors import AppError


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object("app.config")
@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
    from app.routes import bp, wants_html
    app.register_blueprint(bp)

    def respond(err, status):
        body = err.to_dict()
        if wants_html():
            if err.field == "url":
                # Input errors appear under the field, with what the user typed kept.
                submitted = request.form.get("url", "")[:2048]
                return render_template("index.html", error=body["error"],
                                       submitted=submitted), status
            return render_template("error.html", **body), status
        return jsonify(body), status

    @app.errorhandler(AppError)
    def handle_app_error(e):
        return respond(e, e.status)

    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        return respond(AppError("E_INTERNAL"), e.code or 500)

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        return respond(AppError("E_INTERNAL"), 500)

    return app
