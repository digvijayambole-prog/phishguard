from flask import Flask, jsonify

from app.errors import AppError


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object("app.config")

    from app.routes import bp
    app.register_blueprint(bp)

    @app.errorhandler(AppError)
    def handle_app_error(e):
        return jsonify(e.to_dict()), e.status

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        err = AppError("E_INTERNAL")
        return jsonify(err.to_dict()), err.status

    return app
