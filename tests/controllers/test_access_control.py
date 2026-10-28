"""Admin panel only for staff; navigation per role; CSRF (US-21; NFR-05, NFR-06)."""
import pytest

from app import create_app
from app.models.repositories.factory import init_storage
from config import TestConfig
from tests.factories import PASSWORD, log_in


def admin_get_paths(app):
    """Every GET route of the admin blueprint — new admin pages are covered automatically."""
    paths = [
        rule.rule for rule in app.url_map.iter_rules()
        if rule.endpoint.startswith("admin.") and "GET" in rule.methods and not rule.arguments
    ]
    assert paths, "admin blueprint has no GET routes"
    return paths


def test_anonymous_user_is_sent_to_login_from_every_admin_page(app, client, repos):
    # US-21 AC2
    for path in admin_get_paths(app):
        response = client.get(path)
        assert response.status_code == 302, path
        assert "/account/login" in response.headers["Location"]


def test_customer_gets_403_on_every_admin_page(app, client, customer):
    # US-21 AC1
    log_in(client, "kunde@example.com", PASSWORD)
    for path in admin_get_paths(app):
        assert client.get(path).status_code == 403, path


def test_admin_sees_admin_panel(app, client, admin, soup):
    # US-21 AC3 (with data, so templates are rendered with real rows)
    log_in(client, "admin@example.com", PASSWORD)
    for path in admin_get_paths(app):
        assert client.get(path).status_code == 200, path
    assert b"Admin panel" in client.get("/admin/").data


@pytest.mark.parametrize("who,shown,hidden", [
    (None, [b"Log in", b"Register"], [b"Log out", b"My account", b">Admin<"]),
    ("kunde@example.com", [b"My account", b"Log out (Test Kunde)"], [b"Register", b">Admin<"]),
    ("admin@example.com", [b">Admin<", b"Log out (Test Admin)"], [b"Register", b"My account"]),
])
def test_navigation_depends_on_role(client, customer, admin, who, shown, hidden):
    if who:
        log_in(client, who, PASSWORD)
    page = client.get("/menu").data
    for text in shown:
        assert text in page
    for text in hidden:
        assert text not in page


def test_flash_message_after_login(client, customer):
    response = client.post(
        "/account/login", data={"email": "kunde@example.com", "password": PASSWORD}, follow_redirects=True
    )
    assert b"Welcome, Test Kunde." in response.data


def test_post_without_csrf_token_is_rejected(tmp_path):
    # NFR-06: CSRF protection is on outside tests
    class CsrfConfig(TestConfig):
        WTF_CSRF_ENABLED = True

    app = create_app(CsrfConfig, overrides={"DATABASE": str(tmp_path / "csrf.sqlite")})
    init_storage(app.config)
    client = app.test_client()
    assert client.post("/account/login", data={"email": "a@example.com", "password": "x"}).status_code == 400
    assert client.post("/account/logout").status_code == 400
