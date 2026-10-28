"""Shop blueprint: C1 menu by event, C2 shopping cart (phase 5), food item pictures."""
from flask import Blueprint, current_app, redirect, render_template, send_from_directory, url_for

bp = Blueprint("shop", __name__)


@bp.get("/")
def index():
    return redirect(url_for("shop.menu"))


@bp.get("/menu")
def menu():
    """C1: published food items as cards, grouped by kind of event (US-06)."""
    groups = current_app.repos.food_items.list_published_by_category()
    return render_template("shop/menu.html", groups=groups)


@bp.get("/uploads/<path:filename>")
def upload(filename):
    """Food item pictures. send_from_directory refuses paths outside the folder (404)."""
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, max_age=3600)
