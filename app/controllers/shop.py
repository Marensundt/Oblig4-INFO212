"""Shop blueprint: C1 menu by event, C2 shopping cart, food item pictures."""
from flask import Blueprint, current_app, flash, redirect, render_template, send_from_directory, url_for

from app.controllers.cart_session import load_cart, save_cart
from app.controllers.forms import CartQuantityForm
from app.models.cart import estimated_total_nok
from app.models.errors import InvalidQuantity, ItemNotAvailable

bp = Blueprint("shop", __name__)

@bp.app_context_processor
def cart_size():
    """Number of cart lines for the header link."""
    return {"cart_size": len(load_cart())}


@bp.get("/")
def index():
    return redirect(url_for("shop.menu"))


@bp.get("/menu")
def menu():
    """C1: published food items as cards, grouped by kind of event (US-06)."""
    groups = current_app.repos.food_items.list_published_by_category()
    return render_template("shop/menu.html", groups=groups)


# --- C2 Shopping cart ----------------------------------------------------------------------

@bp.get("/cart")
def cart():
    """Cart lines with price × quantity and estimated total (US-09 AC1); drops unpublished items (AC4)."""
    cart = load_cart()
    lines, removed = cart.refresh(current_app.repos.food_items.get_many(cart.item_ids))
    if removed:
        save_cart(cart)
        for name in removed:
            flash(f"“{name}” is no longer on the menu and was removed from your cart." if name
                  else "An item is no longer on the menu and was removed from your cart.", "error")
    return render_template("shop/cart.html", lines=lines, total_nok=estimated_total_nok(lines))


@bp.post("/cart/add")
def cart_add():
    """US-08: add from a menu card; below the minimum order is rejected with a message."""
    form = CartQuantityForm()
    if not form.validate():
        flash("Enter the number of portions as a whole number.", "error")
        return redirect(url_for("shop.menu"))
    item = current_app.repos.food_items.get(form.item_id.data)
    cart = load_cart()
    try:
        if item is None:
            raise ItemNotAvailable("This item is not on the menu.")
        cart.add(item, form.quantity.data)
    except (InvalidQuantity, ItemNotAvailable) as error:
        flash(f"Not added to the cart: {error}", "error")
        return redirect(url_for("shop.menu"))
    save_cart(cart)
    flash(f"Added {form.quantity.data} portions of “{item.name}” to your cart.", "success")
    return redirect(url_for("shop.menu"))


@bp.post("/cart/update")
def cart_update():
    """US-09 AC2: change a quantity; a rejected change keeps the old quantity."""
    form = CartQuantityForm()
    if not form.validate():
        flash("Enter the number of portions as a whole number.", "error")
        return redirect(url_for("shop.cart"))
    item = current_app.repos.food_items.get(form.item_id.data)
    cart = load_cart()
    try:
        if item is None:
            raise ItemNotAvailable("This item is not on the menu.")
        cart.set_quantity(item, form.quantity.data)
    except (InvalidQuantity, ItemNotAvailable) as error:
        flash(f"Not changed: {error}", "error")
        return redirect(url_for("shop.cart"))
    save_cart(cart)
    flash(f"“{item.name}” changed to {form.quantity.data} portions.", "success")
    return redirect(url_for("shop.cart"))


@bp.post("/cart/remove/<int:item_id>")
def cart_remove(item_id):
    """US-09 AC3."""
    cart = load_cart()
    if item_id in cart:
        cart.remove(item_id)
        save_cart(cart)
        flash("The item was removed from your cart.", "success")
    return redirect(url_for("shop.cart"))


@bp.get("/uploads/<path:filename>")
def upload(filename):
    """Food item pictures. send_from_directory refuses paths outside the folder (404)."""
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, max_age=3600)
