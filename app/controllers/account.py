"""Account blueprint: register/login/logout (C3), later C3 order, C4 my orders, C5 questions."""
from urllib.parse import urlsplit

from flask import Blueprint, current_app, flash, g, redirect, render_template, request, session, url_for

from app.controllers.decorators import login_required
from app.controllers.forms import LoginForm, LogoutForm, RegisterForm
from app.models.accounts import authenticate, register_customer
from app.models.errors import DuplicateEmail

bp = Blueprint("account", __name__, url_prefix="/account")

# Session keys that survive logging in, e.g. the shopping cart (US-11 AC2).
KEPT_ON_LOGIN = ("cart",)


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
