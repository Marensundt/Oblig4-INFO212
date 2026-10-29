"""Checkout and order placement (OB4 C3; US-11 AC2, US-12, US-13)."""
import re
from dataclasses import replace
from datetime import date, timedelta

from app.models.enums import Allergen, OrderStatus, PaymentStatus
from tests.factories import PASSWORD, log_in

EVENT_DATE = (date.today() + timedelta(days=30)).isoformat()


def add_to_cart(client, item, quantity=None):
    client.post("/cart/add", data={"item_id": item.id, "quantity": quantity or item.min_order_qty})


def cart_in_session(client):
    with client.session_transaction() as session:
        return session.get("cart")


def order_form(**overrides):
    data = {
        "event_date": EVENT_DATE,
        "guest_count": "30",
        "delivery_address": "Bryggen 1\n5003 Bergen",
        "guest_groups-0-label": "Adults",
        "guest_groups-0-count": "25",
        "guest_groups-0-dietary_notes": "2 vegetarian",
        "guest_groups-1-label": "Children",
        "guest_groups-1-count": "5",
        "guest_groups-1-allergies": ["nuts", "milk"],
        "guest_groups-1-dietary_notes": "",
        "submit": "Send order",
    }
    data.update(overrides)
    return data


def test_anonymous_visitor_is_sent_to_login_and_back_with_cart(client, customer, soup):
    # US-11 AC2
    add_to_cart(client, soup, 12)
    response = client.get("/account/checkout")
    assert response.status_code == 302
    assert "/account/login?next=/account/checkout" in response.headers["Location"]
    response = log_in(client, "kunde@example.com", PASSWORD, next_url="/account/checkout")
    assert response.headers["Location"] == "/account/checkout"
    page = client.get("/account/checkout").data.decode()
    assert "Send your order" in page
    assert cart_in_session(client) == {str(soup.id): 12}


def test_register_from_checkout_returns_to_checkout(client, repos, soup):
    # OB4 C3 "Log in (or register)"
    add_to_cart(client, soup)
    response = client.post("/account/register", data={
        "name": "Ny Kunde", "email": "ny@example.com", "phone": "", "password": "long-enough",
        "confirm": "long-enough", "next": "/account/checkout",
    })
    assert response.headers["Location"] == "/account/checkout"
    assert client.get("/account/checkout").status_code == 200


def test_cart_page_links_to_checkout(client, repos, soup):
    add_to_cart(client, soup)
    assert 'href="/account/checkout"' in client.get("/cart").data.decode()


def test_checkout_form_fields(client, customer, soup):
    # US-12 AC4 no payment step; US-13 AC3 no name field for guests
    add_to_cart(client, soup, 10)
    log_in(client, "kunde@example.com", PASSWORD)
    page = client.get("/account/checkout").data.decode()
    for name in ("event_date", "guest_count", "delivery_address", "guest_groups-0-label",
                 "guest_groups-0-count", "guest_groups-0-allergies", "guest_groups-0-dietary_notes"):
        assert f'name="{name}"' in page
    assert 'type="date"' in page
    assert "1890 NOK" in page  # estimated total of the cart
    assert not re.search(r'name="[^"]*(card|pay)', page)  # no payment fields
    assert "No payment now" in page
    group_fields = set(re.findall(r'name="guest_groups-0-(\w+)"', page))
    assert group_fields == {"label", "count", "allergies", "dietary_notes"}


def test_empty_cart_sends_back_to_menu(client, customer, repos):
    # US-12 AC3
    log_in(client, "kunde@example.com", PASSWORD)
    response = client.get("/account/checkout", follow_redirects=True)
    assert response.request.path == "/menu"
    assert "Your cart is empty" in response.data.decode()
    client.post("/account/checkout", data=order_form())
    assert repos.orders.list() == []


def test_valid_order_is_stored_and_cart_emptied(client, repos, customer, soup):
    # US-12 AC1, US-13 AC1
    add_to_cart(client, soup, 30)
    log_in(client, "kunde@example.com", PASSWORD)
    response = client.post("/account/checkout", data=order_form())
    assert response.status_code == 302

    [order] = repos.orders.list_for_customer(customer.id)
    assert response.headers["Location"] == f"/account/checkout/confirmation/{order.id}"
    assert order.status == OrderStatus.SUBMITTED
    assert order.payment_status == PaymentStatus.NOT_PAID
    assert order.event_date.isoformat() == EVENT_DATE
    assert order.guest_count == 30
    assert order.delivery_address == "Bryggen 1\n5003 Bergen"
    assert [(line.item_name, line.unit_price_nok, line.quantity) for line in order.lines] == [("Fish soup", 189, 30)]
    assert [(g.label, g.count, g.allergies, g.dietary_notes) for g in order.guest_groups] == [
        ("Adults", 25, set(), "2 vegetarian"), ("Children", 5, {Allergen.NUTS, Allergen.MILK}, "")]
    assert cart_in_session(client) is None

    page = client.get(response.headers["Location"]).data.decode()
    assert f"Order {order.order_number} received" in page
    assert "Submitted" in page and "Not paid" in page
    assert "Children" in page and '<span class="badge badge-allergen">Nuts</span>' in page
    assert "5670 NOK" in page


def test_event_date_in_past_rejected(client, repos, customer, soup):
    # US-12 AC2
    add_to_cart(client, soup)
    log_in(client, "kunde@example.com", PASSWORD)
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    response = client.post("/account/checkout", data=order_form(event_date=yesterday))
    assert response.status_code == 200
    assert "The event date must be after today." in response.data.decode()
    assert repos.orders.list() == []
    assert cart_in_session(client) == {str(soup.id): 10}  # cart kept


def test_guests_below_one_rejected(client, repos, customer, soup):
    # US-12 AC2
    add_to_cart(client, soup)
    log_in(client, "kunde@example.com", PASSWORD)
    page = client.post("/account/checkout", data=order_form(guest_count="0")).data.decode()
    assert "The number of guests must be at least 1." in page
    assert repos.orders.list() == []


def test_group_counts_above_guests_rejected(client, repos, customer, soup):
    # US-13 AC2
    add_to_cart(client, soup)
    log_in(client, "kunde@example.com", PASSWORD)
    page = client.post("/account/checkout", data=order_form(guest_count="20")).data.decode()
    assert "The guest groups add up to 30 guests, but the order is for 20." in page
    assert repos.orders.list() == []


def test_missing_fields_are_shown_and_input_kept(client, repos, customer, soup):
    add_to_cart(client, soup)
    log_in(client, "kunde@example.com", PASSWORD)
    page = client.post("/account/checkout", data=order_form(
        delivery_address="", **{"guest_groups-0-label": ""})).data.decode()
    assert "Enter a delivery address." in page
    assert "Name the group" in page
    assert 'value="30"' in page  # guest count kept
    assert repos.orders.list() == []


def test_add_group_button_without_javascript(client, repos, customer, soup):
    add_to_cart(client, soup)
    log_in(client, "kunde@example.com", PASSWORD)
    data = order_form(add_group="Add another guest group")
    del data["submit"]
    page = client.post("/account/checkout", data=data).data.decode()
    assert 'name="guest_groups-2-label"' in page
    assert 'value="Children"' in page  # earlier input kept
    assert repos.orders.list() == []


def test_unpublished_item_sends_back_to_cart(client, repos, customer, soup):
    add_to_cart(client, soup)
    log_in(client, "kunde@example.com", PASSWORD)
    repos.food_items.update(replace(soup, published=False))
    response = client.post("/account/checkout", data=order_form(), follow_redirects=True)
    assert response.request.path == "/cart"
    assert repos.orders.list() == []


def test_admin_cannot_check_out(client, repos, admin, soup):
    add_to_cart(client, soup)
    log_in(client, "admin@example.com", PASSWORD)
    response = client.post("/account/checkout", data=order_form(), follow_redirects=True)
    assert "customer account" in response.data.decode()
    assert repos.orders.list() == []


def test_confirmation_only_for_own_order(client, repos, customer, soup):
    from app.models.entities import User
    from app.models.security import hash_password
    add_to_cart(client, soup, 30)
    log_in(client, "kunde@example.com", PASSWORD)
    client.post("/account/checkout", data=order_form())
    [order] = repos.orders.list()
    client.post("/account/logout")
    repos.users.add(User("annen@example.com", hash_password(PASSWORD), "Annen Kunde"))
    log_in(client, "annen@example.com", PASSWORD)
    assert client.get(f"/account/checkout/confirmation/{order.id}").status_code == 404
    assert client.get("/account/checkout/confirmation/999").status_code == 404


def test_checkout_form_has_csrf_token(app, repos, customer, soup):
    app.config["WTF_CSRF_ENABLED"] = True
    client = app.test_client()
    with client.session_transaction() as session:
        session["cart"] = {str(soup.id): 10}
        session["user_id"] = customer.id
    page = client.get("/account/checkout").data.decode()
    assert 'name="csrf_token"' in page
    assert client.post("/account/checkout", data=order_form()).status_code == 400
