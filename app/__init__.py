"""Ekte Mat Online — Flask application factory.

MVC layout:
  app/models/            model layer: domain classes and all data access (repositories)
  app/views/templates/   view layer: Jinja2 templates
  app/controllers/       controller layer: Flask blueprints shop, account, admin
"""
import os

from flask import Flask, render_template
from flask_wtf import CSRFProtect

from app.models.errors import StorageNotInitialised, StorageUnavailable
from app.models.image_service import build_image_service
from app.models.images import ImageStorage
from app.models.repositories.factory import build_repositories
from config import Config

csrf = CSRFProtect()


def create_app(config_class=Config, overrides=None):
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder="views/templates",
    )
    app.config.from_object(config_class)
    if overrides:
        app.config.update(overrides)
    if not app.config.get("DATABASE"):
        app.config["DATABASE"] = os.path.join(app.instance_path, "ektemat.sqlite")
    if not app.config.get("UPLOAD_FOLDER"):
        # Food item pictures (A2), served on the menu (C1); git-ignored with instance/.
        app.config["UPLOAD_FOLDER"] = os.path.join(app.instance_path, "uploads")
    os.makedirs(app.instance_path, exist_ok=True)

    csrf.init_app(app)

    # Controllers reach storage only through these repositories.
    app.repos = build_repositories(app.config)
    # Food item pictures (A2): files in UPLOAD_FOLDER and the image service (offline placeholder or Claude).
    app.images = ImageStorage(app.config["UPLOAD_FOLDER"])
    app.image_service = build_image_service(app.config)

    from app.cli import register_cli

    register_cli(app)

    from app.controllers.account import bp as account_bp
    from app.controllers.admin import bp as admin_bp
    from app.controllers.shop import bp as shop_bp

    app.register_blueprint(shop_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(admin_bp)

    from app.controllers.decorators import load_current_user

    app.before_request(load_current_user)

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(StorageNotInitialised)
    def storage_not_initialised(error):
        app.logger.error("Database not initialised: %s", error)
        return render_template("errors/database.html"), 503

    @app.errorhandler(StorageUnavailable)
    def storage_unavailable(error):
        app.logger.error("Database unavailable: %s", error)
        return render_template("errors/database.html", unavailable=True), 503

    @app.errorhandler(413)
    def too_large(error):
        return render_template("errors/413.html"), 413

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        # Details go to the log, never to the visitor
        app.logger.exception("Unhandled error: %s", getattr(error, "original_exception", error))
        return render_template("errors/500.html"), 500

    return app
