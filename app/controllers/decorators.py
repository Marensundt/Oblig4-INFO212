"""Access control for controllers (US-11, US-21; NFR-05)."""
from functools import wraps

from flask import abort, current_app, flash, g, redirect, request, session, url_for


def load_current_user():
    """Runs before every request: g.user is the logged-in User or None."""
    user_id = session.get("user_id")
    g.user = current_app.repos.users.get(user_id) if user_id is not None else None


def _redirect_to_login():
    flash("Please log in to continue.", "info")
    next_url = request.full_path.rstrip("?")
    return redirect(url_for("account.login", next=next_url))


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return _redirect_to_login()
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    """Anonymous users are sent to login; logged-in customers get 403 (US-21)."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return _redirect_to_login()
        if not g.user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped
