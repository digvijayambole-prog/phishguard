from flask import Flask, jsonify, render_template
from werkzeug.exceptions import HTTPException

from app.errors import AppError


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object("app.config")

    from app.routes import bp, wants_html
    app.register_blueprint(bp)

    def respond(err, status):
        body = err.to_dict()
        if wants_html():
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
