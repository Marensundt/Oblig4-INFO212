"""Admin order list and order page (OB4 A3; US-14, US-15, US-16)."""
import re
from datetime import date, timedelta

import pytest

from app.models.entities import GuestGroup
from app.models.enums import Allergen, OrderStatus, PaymentStatus
from tests.factories import PASSWORD, log_in, make_order


@pytest.fixture
def admin_client(client, admin):
    log_in(client, "admin@example.com", PASSWORD)
    return client


def order_numbers(page):
    return re.findall(r'<a href="/admin/orders/\d+">([\d-]+)</a>', page)


def add_order(repos, customer, soup, days_ahead=30, status=None, **kwargs):
    order = repos.orders.add(make_order(customer.id, soup, days_ahead=days_ahead, **kwargs))
    path = {
        OrderStatus.APPROVED: ["approved"],
        OrderStatus.IN_PREPARATION: ["approved", "in_preparation"],
        OrderStatus.DELIVERED: ["approved", "in_preparation", "delivered"],
        OrderStatus.REJECTED: ["rejected"],
        OrderStatus.CANCELLED: ["cancelled"],
    }.get(status, [])
    for step in path:
        order = repos.orders.update_status(order.id, step)
    return order


def test_list_shows_all_orders_sorted_by_event_date_with_columns(admin_client, repos, customer, soup):
    # US-14 AC3
    later = add_order(repos, customer, soup, days_ahead=60)
    sooner = add_order(repos, customer, soup, days_ahead=10, guests=15)
    page = admin_client.get("/admin/orders").data.decode()
    assert order_numbers(page) == [sooner.order_number, later.order_number]
    assert "Test Kunde" in page
    assert sooner.event_date.strftime("%d.%m.%Y") in page
    assert "<td class=\"num\">15</td>" in page
    assert ">Submitted<" in page and ">Not paid<" in page
    assert "⚠ Yes" in page  # make_order has a nut allergy


def test_filter_by_status(admin_client, repos, customer, soup):
    # US-14 AC1
    submitted = add_order(repos, customer, soup)
    approved = add_order(repos, customer, soup, status=OrderStatus.APPROVED)
    page = admin_client.get("/admin/orders?status=approved").data.decode()
    assert order_numbers(page) == [approved.order_number]
    assert submitted.order_number not in order_numbers(page)
    assert '<option selected value="approved">' in page


def test_filter_by_event_date_range_inclusive(admin_client, repos, customer, soup):
    # US-14 AC2
    early = add_order(repos, customer, soup, days_ahead=5)
    middle = add_order(repos, customer, soup, days_ahead=20)
    late = add_order(repos, customer, soup, days_ahead=40)
    start = (date.today() + timedelta(days=5)).isoformat()
    end = (date.today() + timedelta(days=20)).isoformat()
    page = admin_client.get(f"/admin/orders?date_from={start}&date_to={end}").data.decode()
    assert order_numbers(page) == [early.order_number, middle.order_number]
    only_from = admin_client.get(f"/admin/orders?date_from={end}").data.decode()
    assert order_numbers(only_from) == [middle.order_number, late.order_number]


def test_filter_status_and_dates_together(admin_client, repos, customer, soup):
    add_order(repos, customer, soup, days_ahead=5, status=OrderStatus.APPROVED)
    wanted = add_order(repos, customer, soup, days_ahead=20, status=OrderStatus.APPROVED)
    add_order(repos, customer, soup, days_ahead=20)
    start = (date.today() + timedelta(days=10)).isoformat()
    page = admin_client.get(f"/admin/orders?status=approved&date_from={start}").data.decode()
    assert order_numbers(page) == [wanted.order_number]


def test_invalid_filter_shows_error_and_all_orders(admin_client, repos, customer, soup):
    order = add_order(repos, customer, soup)
    page = admin_client.get("/admin/orders?date_from=2026-12-10&date_to=2026-12-01").data.decode()
    assert "must be on or after" in page
    assert order_numbers(page) == [order.order_number]
    page = admin_client.get("/admin/orders?status=confimed").data.decode()
    assert "Not a valid choice" in page


def test_no_match_message(admin_client, repos, customer, soup):
    add_order(repos, customer, soup)
    assert "No orders match the filter." in admin_client.get("/admin/orders?status=delivered").data.decode()


def test_order_page_shows_everything_with_allergies_highlighted(admin_client, repos, customer, soup):
    # US-15 AC1
    order = add_order(repos, customer, soup, guests=30)
    order = repos.orders.get(order.id)
    page = admin_client.get(f"/admin/orders/{order.id}").data.decode()
    assert "Test Kunde" in page and "kunde@example.com" in page
    assert order.event_date.strftime("%d.%m.%Y") in page
    assert "Bryggen 1, 5003 Bergen" in page
    assert "Fish soup" in page and f"{189 * 30} NOK" in page
    assert '<div class="allergy-alert" role="note">' in page
    assert "Adults (30 guests): Nuts" in page
    assert 'class="row-allergy"' in page
    assert "1 vegetarian" in page


def test_no_allergy_alert_without_allergies(admin_client, repos, customer, soup):
    order = make_order(customer.id, soup)
    order.guest_groups = [GuestGroup("Adults", 20)]
    order = repos.orders.add(order)
    assert "allergy-alert" not in admin_client.get(f"/admin/orders/{order.id}").data.decode()


def test_status_form_offers_only_allowed_next_statuses(admin_client, repos, customer, soup):
    order = add_order(repos, customer, soup, status=OrderStatus.APPROVED)
    page = admin_client.get(f"/admin/orders/{order.id}").data.decode()
    options = re.findall(r'<option value="(\w+)">', page.split('name="status"')[1].split("</select>")[0])
    assert options == ["in_preparation", "cancelled"]


def test_main_path_through_all_statuses(admin_client, repos, customer, soup):
    # US-15 AC2, AC2b
    order = add_order(repos, customer, soup)
    for status in ("approved", "in_preparation", "delivered"):
        page = admin_client.post(f"/admin/orders/{order.id}/status", data={"status": status},
                                 follow_redirects=True).data.decode()
        assert f"is now {OrderStatus(status).label}" in page
        assert repos.orders.get(order.id).status == status
    assert "is final and cannot be changed" in page


def test_reject_submitted_order(admin_client, repos, customer, soup):
    # US-15 AC2
    order = add_order(repos, customer, soup)
    admin_client.post(f"/admin/orders/{order.id}/status", data={"status": "rejected"})
    assert repos.orders.get(order.id).status == OrderStatus.REJECTED


@pytest.mark.parametrize("final", [OrderStatus.DELIVERED, OrderStatus.REJECTED, OrderStatus.CANCELLED])
def test_final_status_cannot_change(admin_client, repos, customer, soup, final):
    # US-15 AC3
    order = add_order(repos, customer, soup, status=final)
    page = admin_client.post(f"/admin/orders/{order.id}/status", data={"status": "approved"},
                             follow_redirects=True).data.decode()
    assert "cannot change" in page
    assert repos.orders.get(order.id).status == final


def test_illegal_transition_refused(admin_client, repos, customer, soup):
    # e.g. skipping approval: submitted → delivered
    order = add_order(repos, customer, soup)
    page = admin_client.post(f"/admin/orders/{order.id}/status", data={"status": "delivered"},
                             follow_redirects=True).data.decode()
    assert "cannot change from submitted" in page
    assert repos.orders.get(order.id).status == OrderStatus.SUBMITTED


@pytest.mark.parametrize("start", [OrderStatus.SUBMITTED, OrderStatus.APPROVED, OrderStatus.IN_PREPARATION])
def test_cancel_non_final_order(admin_client, repos, customer, soup, start):
    # US-15 AC4
    order = add_order(repos, customer, soup, status=start)
    admin_client.post(f"/admin/orders/{order.id}/status", data={"status": "cancelled"})
    assert repos.orders.get(order.id).status == OrderStatus.CANCELLED


@pytest.mark.parametrize("payment", list(PaymentStatus))
def test_set_payment_status(admin_client, repos, customer, soup, payment):
    # US-16 AC2: stored and shown on order page and list
    order = add_order(repos, customer, soup)
    page = admin_client.post(f"/admin/orders/{order.id}/payment", data={"payment_status": payment.value},
                             follow_redirects=True).data.decode()
    assert repos.orders.get(order.id).payment_status == payment
    assert f'<option selected value="{payment.value}">' in page
    assert f">{payment.label.capitalize()}<" in admin_client.get("/admin/orders").data.decode()


def test_invalid_payment_status_refused(admin_client, repos, customer, soup):
    order = add_order(repos, customer, soup)
    page = admin_client.post(f"/admin/orders/{order.id}/payment", data={"payment_status": "free"},
                             follow_redirects=True).data.decode()
    assert "Choose a valid payment status." in page
    assert repos.orders.get(order.id).payment_status == PaymentStatus.NOT_PAID


def test_unknown_order_is_404(admin_client, repos):
    assert admin_client.get("/admin/orders/999").status_code == 404
    assert admin_client.post("/admin/orders/999/status", data={"status": "approved"}).status_code == 404
    assert admin_client.post("/admin/orders/999/payment", data={"payment_status": "paid"}).status_code == 404


def test_customer_cannot_use_order_routes(client, repos, customer, soup):
    # US-21: routes with an id are not covered by the automatic admin GET test
    order = add_order(repos, customer, soup)
    log_in(client, "kunde@example.com", PASSWORD)
    assert client.get(f"/admin/orders/{order.id}").status_code == 403
    assert client.post(f"/admin/orders/{order.id}/status", data={"status": "approved"}).status_code == 403
    assert client.post(f"/admin/orders/{order.id}/payment", data={"payment_status": "paid"}).status_code == 403
    assert repos.orders.get(order.id).status == OrderStatus.SUBMITTED


def test_dashboard_counts_orders_waiting(admin_client, repos, customer, soup):
    add_order(repos, customer, soup)
    add_order(repos, customer, soup)
    add_order(repos, customer, soup, status=OrderStatus.APPROVED)
    page = admin_client.get("/admin/").data.decode()
    assert "2 new orders waiting for approval" in page
    assert 'href="/admin/orders?status=submitted"' in page


def test_seeded_orders_list(admin_client, repos):
    from app.models.seed import seed
    seed(repos)
    page = admin_client.get("/admin/orders").data.decode()
    assert len(order_numbers(page)) == len(repos.orders.list())
    assert "Kari Kunde" in page and "Ola Kunde" in page
