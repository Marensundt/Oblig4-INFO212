"""Admin blueprint: A1 food items, A2 images, A3 orders, A4 questions (placeholder in phase 0)."""
from flask import Blueprint, render_template

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.get("/")
def index():
    return render_template("admin/index.html")
