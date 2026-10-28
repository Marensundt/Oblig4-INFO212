from datetime import date

import pytest

from app.models.entities import GuestGroup, Order, OrderLine, Question, User
from app.models.enums import OrderStatus, PaymentStatus, Role
from app.models.errors import InvalidStatusTransition
from app.models.security import check_password, hash_password


def make_order(**kwargs):
    defaults = dict(customer_id=1, event_date=date(2027, 5, 1), guest_count=10, delivery_address="Bryggen 1")
    return Order(**{**defaults, **kwargs})


def test_new_order_defaults():
    order = make_order()
    assert order.status == OrderStatus.SUBMITTED
    assert order.payment_status == PaymentStatus.NOT_PAID


def test_order_total_is_computed_from_lines():
    order = make_order(lines=[OrderLine("Soup", 189, 10), OrderLine("Salad", 165, 4)])
    assert order.lines[0].line_total_nok == 1890
    assert order.total_nok == 1890 + 660


def test_change_status_along_main_path():
    order = make_order()
    for status in ("approved", "in_preparation", "delivered"):
        order.change_status(status)
    assert order.status == OrderStatus.DELIVERED


def test_change_status_refuses_illegal_change():
    order = make_order(status=OrderStatus.DELIVERED)
    with pytest.raises(InvalidStatusTransition):
        order.change_status(OrderStatus.SUBMITTED)
    assert order.status == OrderStatus.DELIVERED


def test_guest_group_has_no_name_field():
    assert "name" not in GuestGroup.__dataclass_fields__


def test_question_is_answered():
    question = Question(order_id=1, author_id=1, text="Cancellation terms?")
    assert not question.is_answered
    question.answer_text = "Free until 7 days before."
    assert question.is_answered


def test_user_is_admin():
    assert User("a@example.com", "h", "A", role=Role.ADMIN).is_admin
    assert not User("c@example.com", "h", "C").is_admin


def test_password_is_hashed_not_plain():
    hashed = hash_password("ektemat-demo")
    assert hashed != "ektemat-demo"
    assert check_password(hashed, "ektemat-demo")
    assert not check_password(hashed, "wrong")
