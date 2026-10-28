from dataclasses import replace
from datetime import date, timedelta

import pytest

from app.models.entities import GuestGroup, OrderLine
from app.models.enums import Allergen, OrderStatus, PaymentStatus
from app.models.errors import DataIntegrityError, InvalidStatusTransition, NotFound
from tests.factories import make_order


def test_add_stores_order_lines_and_guest_groups(repos, soup, customer):
    order = make_order(customer.id, soup, guests=30)
    order.guest_groups = [
        GuestGroup("Adults", 25, set(), "2 vegetarian"),
        GuestGroup("Children", 5, {Allergen.NUTS, Allergen.MILK}),
    ]
    stored = repos.orders.add(order)

    assert stored.id is not None
    assert stored.status == OrderStatus.SUBMITTED
    assert stored.payment_status == PaymentStatus.NOT_PAID
    assert stored.total_nok == 189 * 30
    assert [g.label for g in stored.guest_groups] == ["Adults", "Children"]
    assert stored.guest_groups[1].allergies == {Allergen.NUTS, Allergen.MILK}
    assert stored.lines[0].unit_price_nok == 189


def test_order_numbers_are_unique_and_sequential(repos, soup, customer):
    first = repos.orders.add(make_order(customer.id, soup))
    second = repos.orders.add(make_order(customer.id, soup))
    year = f"{date.today():%y}"
    assert first.order_number == f"{year}-0001"
    assert second.order_number == f"{year}-0002"


def test_add_is_one_transaction(repos, soup, customer):
    order = make_order(customer.id, soup)
    order.lines.append(OrderLine("Broken line", 100, 0))  # quantity 0 breaks a rule
    with pytest.raises(DataIntegrityError):
        repos.orders.add(order)
    assert repos.orders.list() == []


@pytest.mark.parametrize("field,value", [("guest_count", 0), ("status", "confimed")])
def test_invalid_order_values_refused(repos, soup, customer, field, value):
    # guests >= 1 (DV-01, ASSUMPTION); status from the official list (DV-07)
    with pytest.raises((DataIntegrityError, ValueError)):
        repos.orders.add(replace(make_order(customer.id, soup), **{field: value}))


def test_guest_group_count_must_be_positive(repos, soup, customer):
    order = make_order(customer.id, soup)
    order.guest_groups = [GuestGroup("Nobody", 0)]
    with pytest.raises(DataIntegrityError):
        repos.orders.add(order)


def test_get_missing_returns_none(repos):
    assert repos.orders.get(999) is None


def test_list_filters_by_status_and_date_sorted_by_event_date(repos, soup, customer):
    late = repos.orders.add(make_order(customer.id, soup, days_ahead=60))
    early = repos.orders.add(make_order(customer.id, soup, days_ahead=10))
    repos.orders.update_status(late.id, OrderStatus.APPROVED)

    assert [o.id for o in repos.orders.list()] == [early.id, late.id]
    assert [o.id for o in repos.orders.list(status=OrderStatus.APPROVED)] == [late.id]
    assert [o.id for o in repos.orders.list(status="submitted")] == [early.id]

    today = date.today()
    assert [o.id for o in repos.orders.list(date_from=today + timedelta(days=30))] == [late.id]
    assert [o.id for o in repos.orders.list(date_to=today + timedelta(days=30))] == [early.id]
    assert repos.orders.list(date_from=today + timedelta(days=11), date_to=today + timedelta(days=59)) == []


def test_list_for_customer_returns_only_own_orders(repos, soup, customer, admin):
    own = repos.orders.add(make_order(customer.id, soup))
    repos.orders.add(make_order(admin.id, soup))
    assert [o.id for o in repos.orders.list_for_customer(customer.id)] == [own.id]


def test_update_status_follows_main_path(repos, soup, customer):
    order = repos.orders.add(make_order(customer.id, soup))
    for status in (OrderStatus.APPROVED, OrderStatus.IN_PREPARATION, OrderStatus.DELIVERED):
        order = repos.orders.update_status(order.id, status)
    assert order.status == OrderStatus.DELIVERED


def test_update_status_refuses_illegal_change(repos, soup, customer):
    order = repos.orders.add(make_order(customer.id, soup))
    repos.orders.update_status(order.id, OrderStatus.REJECTED)
    with pytest.raises(InvalidStatusTransition):
        repos.orders.update_status(order.id, OrderStatus.APPROVED)
    assert repos.orders.get(order.id).status == OrderStatus.REJECTED


def test_update_status_missing_order(repos):
    with pytest.raises(NotFound):
        repos.orders.update_status(999, OrderStatus.APPROVED)


def test_update_payment_status_any_value(repos, soup, customer):
    order = repos.orders.add(make_order(customer.id, soup))
    for payment in (PaymentStatus.PAID, PaymentStatus.DEPOSIT_PAID, PaymentStatus.INVOICED):
        assert repos.orders.update_payment_status(order.id, payment).payment_status == payment
    with pytest.raises(NotFound):
        repos.orders.update_payment_status(999, PaymentStatus.PAID)
    with pytest.raises(ValueError):
        repos.orders.update_payment_status(order.id, "refunded")
