import os

from flask import Flask, jsonify, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from app.errors import AppError

limiter = Limiter(key_func=get_remote_address, default_limits=[])


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object("app.config")
    limiter.init_app(app)

    # Behind a trusted proxy (e.g. Render) set PROXY_HOPS=1 so each visitor is
    # rate-limited by their own address. Ignored by default, so a spoofed header
    # cannot dodge the limit when running locally.
    hops = os.environ.get("PROXY_HOPS", "0").strip()
    if hops.isdigit() and int(hops) > 0:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=int(hops), x_proto=int(hops))

    # Temporary diagnostic: set LOG_PROXY=1 to print the proxy headers once, so the
    # right PROXY_HOPS value can be read off. Off by default. Turn it off afterwards.
    if os.environ.get("LOG_PROXY") == "1":
        @app.before_request
        def log_proxy_headers():
            print("PROXYDEBUG xff=%r remote=%r" % (
                request.headers.get("X-Forwarded-For"), request.remote_addr), flush=True)

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
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
        code = "E_RATE_LIMIT" if e.code == 429 else "E_INTERNAL"
        return respond(AppError(code), e.code or 500)

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        return respond(AppError("E_INTERNAL"), 500)

    return app
