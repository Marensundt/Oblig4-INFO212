"""Admin blueprint: A1 food items, A2 images, A3 orders, A4 questions. Staff only (US-21)."""
from flask import Blueprint, render_template

from app.controllers.decorators import admin_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.get("/")
@admin_required
def index():
    return render_template("admin/index.html")
