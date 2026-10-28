"""Registration and authentication (US-10, US-11; NFR-04)."""
import pytest

from app.models.accounts import authenticate, register_customer
from app.models.enums import Role
from app.models.errors import DuplicateEmail


def test_register_creates_customer_with_hashed_password(repos):
    user = register_customer(repos, " Kari Kunde ", "Kari@Example.com", "secret-pass", phone=" ")
    assert user.id is not None
    assert user.role == Role.CUSTOMER
    assert user.name == "Kari Kunde"
    assert user.email == "kari@example.com"
    assert user.phone is None
    assert user.password_hash != "secret-pass"  # US-10 AC3


def test_register_refuses_duplicate_email(repos):
    register_customer(repos, "Kari", "kari@example.com", "secret-pass")
    with pytest.raises(DuplicateEmail):
        register_customer(repos, "Kari 2", "KARI@example.com", "other-pass")


def test_register_refuses_short_password(repos):
    with pytest.raises(ValueError):
        register_customer(repos, "Kari", "kari@example.com", "short")
    assert repos.users.get_by_email("kari@example.com") is None


def test_authenticate(repos):
    user = register_customer(repos, "Kari", "kari@example.com", "secret-pass")
    assert authenticate(repos, "KARI@example.com", "secret-pass") == user
    assert authenticate(repos, "kari@example.com", "wrong-pass") is None
    assert authenticate(repos, "nobody@example.com", "secret-pass") is None
