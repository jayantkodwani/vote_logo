"""Application factory for the LTC Fund Swift Capital Call — Logo Vote app."""

import os

from flask import Flask

from .models import db


def _database_uri() -> str:
    """Pick a database. Priority:
    1) DATABASE_URL env (e.g. Azure Database for PostgreSQL)
    2) SQLite on Azure's persistent /home storage (survives restarts)
    3) Local ./instance/logo_votes.db for development
    """
    url = os.environ.get("DATABASE_URL")
    if url:
        # SQLAlchemy needs the postgresql:// scheme
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    on_azure = bool(os.environ.get("WEBSITE_SITE_NAME"))
    if on_azure:
        data_dir = "/home/data"
    else:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance")
    os.makedirs(data_dir, exist_ok=True)
    return "sqlite:///" + os.path.join(data_dir, "logo_votes.db")


def create_app() -> Flask:
    app = Flask(__name__)

    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-insecure-change-me"),
        SQLALCHEMY_DATABASE_URI=_database_uri(),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        # Comma-separated list of admin emails allowed to reset votes.
        ADMIN_EMAILS=[
            e.strip().lower()
            for e in os.environ.get("ADMIN_EMAILS", "").split(",")
            if e.strip()
        ],
    )
    if os.environ.get("WEBSITE_SITE_NAME"):
        # Behind Azure's HTTPS front end.
        app.config["SESSION_COOKIE_SECURE"] = True

    db.init_app(app)
    with app.app_context():
        db.create_all()

    from .views import bp
    app.register_blueprint(bp)

    return app
