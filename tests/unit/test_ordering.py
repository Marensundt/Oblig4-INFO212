"""Order rules for checkout (OB4 C3; US-12, US-13)."""
from dataclasses import replace
from datetime import date, timedelta

import pytest

from app.models.cart import Cart
from app.models.entities import GuestGroup
from app.models.enums import Allergen, OrderStatus, PaymentStatus
from app.models.errors import InvalidOrder
from app.models.ordering import MAX_GUEST_GROUPS, check_cart, place_order

TODAY = date(2026, 11, 1)
NEXT_MONTH = TODAY + timedelta(days=30)


def order(repos, customer, cart, event_date=NEXT_MONTH, guests=20, address="Bryggen 1, 5003 Bergen",
          groups=None):
    groups = groups if groups is not None else [GuestGroup("Adults", guests)]
    return place_order(repos, customer, cart, event_date, guests, address, groups, today=TODAY)


def test_valid_order_is_stored_submitted_and_not_paid(repos, customer, soup):
    # US-12 AC1
    stored = order(repos, customer, Cart({soup.id: 20}), groups=[
        GuestGroup("Adults", 15, set(), "2 vegetarian"),
        GuestGroup("Children", 5, {Allergen.NUTS}),
    ])
    assert stored.order_number
    assert stored.customer_id == customer.id
    assert stored.status == OrderStatus.SUBMITTED
    assert stored.payment_status == PaymentStatus.NOT_PAID
    assert [(line.item_name, line.unit_price_nok, line.quantity) for line in stored.lines] == [("Fish soup", 189, 20)]
    assert stored.total_nok == 189 * 20
    # US-13 AC1: every group stored with allergies and notes
    assert [(g.label, g.count, g.allergies, g.dietary_notes) for g in stored.guest_groups] == [
        ("Adults", 15, set(), "2 vegetarian"), ("Children", 5, {Allergen.NUTS}, "")]
    assert repos.orders.get(stored.id) == stored


def test_price_is_copied_onto_order(repos, customer, soup):
    # US-02 AC2: later price changes do not change the order
    stored = order(repos, customer, Cart({soup.id: 10}))
    repos.food_items.update(replace(soup, price_nok=250))
    assert repos.orders.get(stored.id).lines[0].unit_price_nok == 189


def test_cart_passed_in_is_not_changed(repos, customer, soup):
    cart = Cart({soup.id: 10})
    order(repos, customer, cart)
    assert cart.quantities == {soup.id: 10}  # the controller empties the session cart


@pytest.mark.parametrize("event_date", [TODAY, TODAY - timedelta(days=1)])
def test_event_date_must_be_after_today(repos, customer, soup, event_date):
    # US-12 AC2 / DV-04
    with pytest.raises(InvalidOrder) as error:
        order(repos, customer, Cart({soup.id: 10}), event_date=event_date)
    assert "event_date" in error.value.errors
    assert repos.orders.list() == []


def test_guests_below_one_rejected(repos, customer, soup):
    # US-12 AC2 / DV-01
    with pytest.raises(InvalidOrder) as error:
        order(repos, customer, Cart({soup.id: 10}), guests=0, groups=[GuestGroup("Adults", 1)])
    assert "guest_count" in error.value.errors


def test_all_errors_reported_together(repos, customer, soup):
    with pytest.raises(InvalidOrder) as error:
        order(repos, customer, Cart({soup.id: 10}), event_date=TODAY, address="  ", groups=[])
    assert set(error.value.errors) == {"event_date", "delivery_address", "guest_groups"}


def test_group_counts_above_guests_rejected(repos, customer, soup):
    # US-13 AC2
    with pytest.raises(InvalidOrder, match="add up to 25 guests, but the order is for 20"):
        order(repos, customer, Cart({soup.id: 10}), groups=[GuestGroup("Adults", 20), GuestGroup("Kids", 5)])


def test_group_counts_below_guests_allowed(repos, customer, soup):
    # Groups describe the guests with special needs; the rest need not be listed (ASSUMPTION)
    stored = order(repos, customer, Cart({soup.id: 10}), guests=40, groups=[GuestGroup("Nut allergy", 2, {Allergen.NUTS})])
    assert stored.guest_count == 40


@pytest.mark.parametrize("groups,message", [
    ([], "at least one guest group"),
    ([GuestGroup(" ", 5)], "needs a name"),
    ([GuestGroup("Adults", 0)], "at least 1 guest"),
    ([GuestGroup("G", 1)] * (MAX_GUEST_GROUPS + 1), "at most"),
])
def test_invalid_guest_groups(repos, customer, soup, groups, message):
    with pytest.raises(InvalidOrder, match=message):
        order(repos, customer, Cart({soup.id: 10}), guests=100, groups=groups)


def test_empty_cart_rejected(repos, customer):
    with pytest.raises(InvalidOrder, match="empty"):
        order(repos, customer, Cart())


def test_unpublished_item_in_cart_rejected(repos, customer, soup):
    repos.food_items.update(replace(soup, published=False))
    with pytest.raises(InvalidOrder, match="no longer on the menu"):
        order(repos, customer, Cart({soup.id: 10}))


def test_raised_minimum_rechecked(repos, customer, soup):
    # OB4 C2 minimum still holds at checkout
    repos.food_items.update(replace(soup, min_order_qty=30))
    with pytest.raises(InvalidOrder, match="Below the minimum order: Fish soup"):
        order(repos, customer, Cart({soup.id: 10}))


def test_check_cart_returns_lines(repos, soup):
    lines = check_cart(repos, Cart({soup.id: 12}))
    assert [(line.item.id, line.quantity) for line in lines] == [(soup.id, 12)]
