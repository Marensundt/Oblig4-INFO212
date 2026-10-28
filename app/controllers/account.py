"""Account blueprint: login/register, C3 order, C4 my orders, C5 questions (placeholder in phase 0)."""
from flask import Blueprint, render_template

bp = Blueprint("account", __name__, url_prefix="/account")


@bp.get("/")
def index():
    return render_template("account/index.html")
