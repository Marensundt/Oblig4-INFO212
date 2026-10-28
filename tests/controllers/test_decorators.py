"""login_required / admin_required on throw-away test routes (US-11, US-21)."""
import pytest

from app.controllers.decorators import admin_required, login_required


@pytest.fixture
def app_with_routes(app):
    app.add_url_rule("/_test/member", "member", login_required(lambda: "member page"))
    app.add_url_rule("/_test/staff", "staff", admin_required(lambda: "staff page"))
    return app


def log_in_as(client, user):
    with client.session_transaction() as session:
        session["user_id"] = user.id


def test_anonymous_is_sent_to_login_with_next(app_with_routes, repos):
    client = app_with_routes.test_client()
    for path in ("/_test/member", "/_test/staff?x=1"):
        response = client.get(path)
        assert response.status_code == 302
        assert "/account/login" in response.headers["Location"]
        assert "next=" in response.headers["Location"]


def test_customer_can_open_login_required_but_not_admin_required(app_with_routes, customer):
    client = app_with_routes.test_client()
    log_in_as(client, customer)
    assert client.get("/_test/member").data == b"member page"
    response = client.get("/_test/staff")
    assert response.status_code == 403
    assert b"Access denied" in response.data


def test_admin_can_open_both(app_with_routes, admin):
    client = app_with_routes.test_client()
    log_in_as(client, admin)
    assert client.get("/_test/member").status_code == 200
    assert client.get("/_test/staff").data == b"staff page"


def test_session_for_deleted_user_counts_as_logged_out(app_with_routes, repos):
    client = app_with_routes.test_client()
    with client.session_transaction() as session:
        session["user_id"] = 999
    assert client.get("/_test/member").status_code == 302
