"""My orders (OB4 C4; US-17)."""
from app.models.entities import User
from app.models.enums import OrderStatus, PaymentStatus
from app.models.security import hash_password
from tests.factories import PASSWORD, log_in, make_order


def other_customer(repos):
    return repos.users.add(User("annen@example.com", hash_password(PASSWORD), "Annen Kunde"))


def test_my_orders_needs_login(client, repos):
    response = client.get("/account/orders")
    assert response.status_code == 302
    assert "/account/login" in response.headers["Location"]


def test_my_orders_lists_only_own_orders(client, repos, customer, soup):
    # US-17 AC1
    mine = repos.orders.add(make_order(customer.id, soup, guests=20))
    theirs = repos.orders.add(make_order(other_customer(repos).id, soup))
    log_in(client, "kunde@example.com", PASSWORD)
    page = client.get("/account/orders").data.decode()
    assert mine.order_number in page
    assert theirs.order_number not in page
    assert mine.event_date.strftime("%d.%m.%Y") in page
    assert ">Submitted<" in page and ">Not paid<" in page
    assert f'href="/account/orders/{mine.id}"' in page


def test_my_orders_empty(client, customer):
    log_in(client, "kunde@example.com", PASSWORD)
    assert "You have no orders yet." in client.get("/account/orders").data.decode()


def test_order_page_shows_details(client, repos, customer, soup):
    order = repos.orders.add(make_order(customer.id, soup, guests=20))
    log_in(client, "kunde@example.com", PASSWORD)
    page = client.get(f"/account/orders/{order.id}").data.decode()
    assert f"Order {order.order_number}" in page
    assert "Fish soup" in page and "3780 NOK" in page
    assert '<span class="badge badge-allergen">Nuts</span>' in page
    assert "Bryggen 1, 5003 Bergen" in page


def test_other_customers_order_is_not_found(client, repos, customer, soup):
    # US-17 AC2
    theirs = repos.orders.add(make_order(other_customer(repos).id, soup))
    log_in(client, "kunde@example.com", PASSWORD)
    assert client.get(f"/account/orders/{theirs.id}").status_code == 404
    assert client.get("/account/orders/999").status_code == 404


def test_admin_change_is_visible_to_customer(client, repos, customer, admin, soup):
    # US-17 AC3 / 01-plan §8 phase 7 acceptance, end to end through both panels
    order = repos.orders.add(make_order(customer.id, soup))
    log_in(client, "admin@example.com", PASSWORD)
    client.post(f"/admin/orders/{order.id}/status", data={"status": "approved"})
    client.post(f"/admin/orders/{order.id}/payment", data={"payment_status": "deposit_paid"})
    client.post("/account/logout")

    log_in(client, "kunde@example.com", PASSWORD)
    page = client.get("/account/orders").data.decode()
    assert ">Approved<" in page and ">Deposit paid<" in page
    stored = repos.orders.get(order.id)
    assert (stored.status, stored.payment_status) == (OrderStatus.APPROVED, PaymentStatus.DEPOSIT_PAID)


def test_header_links_to_my_orders_for_customer(client, customer):
    log_in(client, "kunde@example.com", PASSWORD)
    assert 'href="/account/orders">My orders</a>' in client.get("/menu").data.decode()


def test_confirmation_links_to_my_orders(client, repos, customer, soup):
    order = repos.orders.add(make_order(customer.id, soup))
    log_in(client, "kunde@example.com", PASSWORD)
    page = client.get(f"/account/checkout/confirmation/{order.id}").data.decode()
    assert 'href="/account/orders"' in page
