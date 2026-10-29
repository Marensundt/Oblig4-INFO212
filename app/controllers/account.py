"""Account blueprint: register/login/logout and checkout (C3), my orders (C4), later C5 questions."""
from urllib.parse import urlsplit

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, session, url_for

from app.controllers.cart_session import CART_KEY, clear_cart, load_cart
from app.controllers.decorators import login_required
from app.controllers.forms import CheckoutForm, LoginForm, LogoutForm, RegisterForm
from app.models.accounts import authenticate, register_customer
from app.models.cart import estimated_total_nok
from app.models.entities import GuestGroup
from app.models.enums import Allergen
from app.models.errors import DuplicateEmail, InvalidOrder
from app.models.ordering import check_cart, place_order

bp = Blueprint("account", __name__, url_prefix="/account")

# Session keys that survive logging in, e.g. the shopping cart (US-11 AC2).
KEPT_ON_LOGIN = (CART_KEY,)


def _safe_next(url):
    """Only allow redirects to paths on this site (no open redirect)."""
    if not url:
        return None
    parts = urlsplit(url)
    if parts.scheme or parts.netloc or not url.startswith("/") or url.startswith("//"):
        return None
    return url


def _start_session(user):
    kept = {key: session[key] for key in KEPT_ON_LOGIN if key in session}
    session.clear()  # new session on login (protects against session fixation)
    session.update(kept)
    session["user_id"] = user.id


def _after_login_url(user, next_url):
    if next_url:
        return next_url
    return url_for("admin.index") if user.is_admin else url_for("account.index")


@bp.get("/")
@login_required
def index():
    return render_template("account/index.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if g.user is not None:
        return redirect(url_for("account.index"))
    form = RegisterForm(next=request.args.get("next", ""))
    if form.validate_on_submit():
        try:
            user = register_customer(
                current_app.repos, form.name.data, form.email.data, form.password.data, form.phone.data
            )
        except DuplicateEmail:
            form.email.errors.append("An account with this e-mail already exists. Log in instead.")
        else:
            _start_session(user)
            flash("Your account has been created. You are now logged in.", "success")
            return redirect(_after_login_url(user, _safe_next(form.next.data)))
    return render_template("account/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(next=request.args.get("next", ""))
    if form.validate_on_submit():
        user = authenticate(current_app.repos, form.email.data, form.password.data)
        if user is None:
            form.password.errors.append("Wrong e-mail or password.")  # US-11 AC1: no hint which one
        else:
            _start_session(user)
            flash(f"Welcome, {user.name}.", "success")
            return redirect(_after_login_url(user, _safe_next(form.next.data)))
    return render_template("account/login.html", form=form)


@bp.post("/logout")
def logout():
    if LogoutForm().validate_on_submit():
        session.clear()
        flash("You have been logged out.", "info")
    return redirect(url_for("shop.menu"))


# --- C3 Checkout -----------------------------------------------------------------------------

def _guest_groups_from(form):
    return [
        GuestGroup(
            label=entry.form.label.data.strip(),
            count=entry.form.count.data,
            allergies={Allergen(a) for a in entry.form.allergies.data or []},
            dietary_notes=(entry.form.dietary_notes.data or "").strip(),
        )
        for entry in form.guest_groups
    ]


@bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    """US-12, US-13: order form for the cart. Anonymous visitors log in first and come back (US-11 AC2)."""
    if g.user.is_admin:
        flash("Orders are placed with a customer account.", "error")
        return redirect(url_for("shop.cart"))
    if not len(load_cart()):
        flash("Your cart is empty. Add food from the menu first.", "info")  # US-12 AC3
        return redirect(url_for("shop.menu"))
    try:
        lines = check_cart(current_app.repos, load_cart())
    except InvalidOrder as error:
        # Items unpublished or below a raised minimum: the cart page explains and fixes it
        flash(error.errors["cart"], "error")
        return redirect(url_for("shop.cart"))

    form = CheckoutForm()
    form_errors = []
    if form.add_group.data:
        # "Add another guest group" without JavaScript: re-show the form with one more row
        if len(form.guest_groups) < form.guest_groups.max_entries:
            form.guest_groups.append_entry()
    elif form.validate_on_submit():
        try:
            order = place_order(current_app.repos, g.user, load_cart(), form.event_date.data,
                                form.guest_count.data, form.delivery_address.data, _guest_groups_from(form))
        except InvalidOrder as error:
            for key, message in error.errors.items():
                field = getattr(form, key, None)
                if key in ("event_date", "guest_count", "delivery_address") and field is not None:
                    field.errors.append(message)
                else:
                    form_errors.append(message)
        else:
            clear_cart()
            flash(f"Thank you! Your order {order.order_number} has been sent to Ekte Mat.", "success")
            return redirect(url_for("account.confirmation", order_id=order.id))
    return render_template("account/checkout.html", form=form, form_errors=form_errors, lines=lines,
                           total_nok=estimated_total_nok(lines))


def _own_order_or_404(order_id):
    """Customers only see their own orders; others' orders are "not found" (US-17 AC2)."""
    order = current_app.repos.orders.get(order_id)
    if order is None or order.customer_id != g.user.id:
        abort(404)
    return order


@bp.get("/checkout/confirmation/<int:order_id>")
@login_required
def confirmation(order_id):
    """US-12 AC1, US-13 AC1: order number, lines and guest groups."""
    return render_template("account/confirmation.html", order=_own_order_or_404(order_id))


# --- C4 My orders ----------------------------------------------------------------------------

@bp.get("/orders")
@login_required
def orders():
    """US-17 AC1, AC3: own orders with current status and payment status."""
    return render_template("account/orders.html", orders=current_app.repos.orders.list_for_customer(g.user.id))


@bp.get("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    return render_template("account/order_detail.html", order=_own_order_or_404(order_id))
