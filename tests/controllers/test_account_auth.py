"""Register, log in, log out (OB4 C3 "Log in (or register)"; US-10, US-11)."""
from app.models.security import check_password
from tests.factories import PASSWORD, log_in

REGISTRATION = {
    "name": "Ny Kunde",
    "email": "ny.kunde@example.com",
    "phone": "",
    "password": "long-enough",
    "confirm": "long-enough",
}


def test_login_and_register_pages_render(client, repos):
    for path in ("/account/login", "/account/register"):
        response = client.get(path)
        assert response.status_code == 200
        assert b"<form" in response.data
        assert b'<label for="email">' in response.data


def test_register_creates_account_and_logs_in(client, repos):
    # US-10 AC1
    response = client.post("/account/register", data=REGISTRATION)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/account/")
    user = repos.users.get_by_email("ny.kunde@example.com")
    assert user is not None and not user.is_admin
    assert check_password(user.password_hash, "long-enough")  # stored as hash (US-10 AC3)
    page = client.get("/account/")
    assert b"Ny Kunde" in page.data


def test_register_with_existing_email_fails(client, customer):
    # US-10 AC2
    response = client.post("/account/register", data={**REGISTRATION, "email": "KUNDE@example.com"})
    assert response.status_code == 200
    assert b"already exists" in response.data
    assert len(client.application.repos.users.list_customers()) == 1


def test_register_validates_input(client, repos):
    response = client.post(
        "/account/register",
        data={**REGISTRATION, "email": "not-an-email", "password": "short", "confirm": "different"},
    )
    assert response.status_code == 200
    assert b"Enter a valid e-mail address." in response.data
    assert b"Use at least 8 characters." in response.data
    assert repos.users.list_customers() == []


def test_customer_login_goes_to_account(client, customer):
    response = log_in(client, "kunde@example.com", PASSWORD)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/account/")
    with client.session_transaction() as session:
        assert session["user_id"] == customer.id


def test_admin_login_goes_to_admin_panel(client, admin):
    response = log_in(client, "admin@example.com", PASSWORD)
    assert response.headers["Location"].endswith("/admin/")


def test_wrong_password_gives_general_error(client, customer):
    # US-11 AC1: same message for wrong password and unknown e-mail
    wrong_password = log_in(client, "kunde@example.com", "wrong-password")
    unknown_email = log_in(client, "nobody@example.com", PASSWORD)
    for response in (wrong_password, unknown_email):
        assert response.status_code == 200
        assert b"Wrong e-mail or password." in response.data
    with client.session_transaction() as session:
        assert "user_id" not in session


def test_login_returns_to_next_page_and_keeps_cart(client, customer):
    # US-11 AC2: return to the page that needed login (e.g. checkout) with the cart unchanged
    with client.session_transaction() as session:
        session["cart"] = {"1": 10}
    response = log_in(client, "kunde@example.com", PASSWORD, next_url="/account/?from=checkout")
    assert response.headers["Location"].endswith("/account/?from=checkout")
    with client.session_transaction() as session:
        assert session["cart"] == {"1": 10}


def test_login_ignores_external_next_url(client, customer):
    for bad in ("https://evil.example/", "//evil.example/", "javascript:alert(1)"):
        response = log_in(client, "kunde@example.com", PASSWORD, next_url=bad)
        assert response.headers["Location"].endswith("/account/")


def test_login_required_page_redirects_back_after_login(client, customer):
    redirect = client.get("/account/")
    assert "/account/login?next=/account/" in redirect.headers["Location"]
    login_page = client.get(redirect.headers["Location"])
    assert b'value="/account/"' in login_page.data  # next carried in the form


def test_logout(client, customer):
    # US-11 AC3
    log_in(client, "kunde@example.com", PASSWORD)
    response = client.post("/account/logout")
    assert response.headers["Location"].endswith("/menu")
    assert client.get("/account/").status_code == 302


def test_logged_in_user_visiting_register_is_redirected(client, customer):
    log_in(client, "kunde@example.com", PASSWORD)
    assert client.get("/account/register").status_code == 302
