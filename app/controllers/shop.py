"""Shop blueprint: C1 menu by event and C2 shopping cart (placeholders in phase 0)."""
from flask import Blueprint, redirect, render_template, url_for

bp = Blueprint("shop", __name__)


@bp.get("/")
def index():
    return redirect(url_for("shop.menu"))


@bp.get("/menu")
def menu():
    return render_template("shop/menu.html")
