"""Order status rules (OB4 A3; OPEN-9 in docs/plans/03)."""
import pytest

from app.models.enums import OrderStatus as S
from app.models.enums import PaymentStatus

ALLOWED = {
    (S.SUBMITTED, S.APPROVED),
    (S.SUBMITTED, S.REJECTED),
    (S.SUBMITTED, S.CANCELLED),
    (S.APPROVED, S.IN_PREPARATION),
    (S.APPROVED, S.CANCELLED),
    (S.IN_PREPARATION, S.DELIVERED),
    (S.IN_PREPARATION, S.CANCELLED),
}
ALL_PAIRS = [(a, b) for a in S for b in S]


def test_official_status_values():
    assert [s.value for s in S] == [
        "submitted", "approved", "in_preparation", "delivered", "rejected", "cancelled",
    ]


def test_official_payment_status_values():
    assert [p.value for p in PaymentStatus] == ["not_paid", "deposit_paid", "invoiced", "paid"]


@pytest.mark.parametrize("current,new", sorted(ALLOWED))
def test_allowed_transitions(current, new):
    assert current.can_change_to(new)


@pytest.mark.parametrize("current,new", [p for p in ALL_PAIRS if p not in ALLOWED])
def test_forbidden_transitions(current, new):
    assert not current.can_change_to(new)


def test_final_states():
    assert {s for s in S if s.is_final} == {S.DELIVERED, S.REJECTED, S.CANCELLED}


def test_can_change_to_accepts_string_value():
    assert S.SUBMITTED.can_change_to("approved")


def test_unknown_status_is_rejected():
    with pytest.raises(ValueError):
        S.SUBMITTED.can_change_to("confimed")  # misspelling found in the order export (DV-07)
