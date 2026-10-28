"""Ekte Mat Online — Flask application factory.

MVC layout:
  app/models/            model layer: domain classes and all data access (repositories)
  app/views/templates/   view layer: Jinja2 templates
  app/controllers/       controller layer: Flask blueprints shop, account, admin
"""
import os

from flask import Flask, render_template
from flask_wtf import CSRFProtect

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
    os.makedirs(app.instance_path, exist_ok=True)

    csrf.init_app(app)

    # Controllers reach storage only through these repositories.
    app.repos = build_repositories(app.config)

    from app.controllers.account import bp as account_bp
    from app.controllers.admin import bp as admin_bp
    from app.controllers.shop import bp as shop_bp

    app.register_blueprint(shop_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(admin_bp)

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    return app
