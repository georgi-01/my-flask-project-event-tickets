import logging
import os
import socket

from flask import Flask, jsonify, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

from app.db import init_db
from app.errors import AppError
from app.labels import TICKET_STATUSES, TICKET_TYPES, VENUE_TYPES


def create_app():
    app = Flask(__name__)
    secret = os.environ.get("SECRET_KEY")
    if not secret:
        if os.environ.get("TESTING") == "1":
            secret = "testing"
        else:
            raise RuntimeError("SECRET_KEY is not set")
    app.config["SECRET_KEY"] = secret
    app.config["TESTING"] = os.environ.get("TESTING") == "1"
    app.config["PROPAGATE_EXCEPTIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 1_000_000
    app.json.ensure_ascii = False
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    init_db()

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "replica": socket.gethostname()})

    @app.context_processor
    def inject():
        endpoint = request.endpoint or ""
        if endpoint.startswith("pages.ticket"):
            nav = "tickets"
        elif endpoint.startswith("pages.desk"):
            nav = "desks"
        elif endpoint.startswith("pages.activity"):
            nav = "activity"
        else:
            nav = "program"
        replica = socket.gethostname()
        return {
            "nav": nav,
            "replica": replica,
            "venue_types": list(VENUE_TYPES.items()),
            "ticket_types": list(TICKET_TYPES.items()),
            "ticket_statuses": list(TICKET_STATUSES.items()),
            "footer": [
                ("контейнер", replica),
                ("протокол", "HTTPS"),
                ("сертификат", "self-signed"),
                ("сървър", "Gunicorn"),
                ("балансьор", "Nginx"),
                ("реплики", "2"),
                ("база", "PostgreSQL"),
                ("опашка", "RabbitMQ"),
                ("работник", "worker"),
                ("дневници", "Dozzle :9998"),
            ],
        }

    @app.errorhandler(AppError)
    def handle_app_error(err):
        if request.path.startswith("/api/"):
            return jsonify({"error": err.message}), err.status
        return render_template("error.html", title="Грешка", message=err.message), err.status

    @app.errorhandler(404)
    def missing(_err):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Не е намерено."}), 404
        return render_template("error.html", title="Липсва", message="Страницата не е намерена."), 404

    @app.errorhandler(500)
    def crashed(_err):
        app.logger.exception("server error")
        if request.path.startswith("/api/"):
            return jsonify({"error": "Грешка в сървъра."}), 500
        return render_template("error.html", title="Грешка", message="Нещо се обърка."), 500

    from app.api import bp as api_bp
    from app.pages import bp as pages_bp

    app.register_blueprint(api_bp)
    app.register_blueprint(pages_bp)
    app.logger.info("ready replica=%s", socket.gethostname())
    return app
