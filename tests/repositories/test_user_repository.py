import pytest

from app.models.entities import User
from app.models.enums import Role
from app.models.errors import DuplicateEmail


def test_add_and_get(repos):
    user = repos.users.add(User("Kari@Example.com", "hash", "Kari", phone="99999999"))
    assert user.id is not None
    assert user.created_at is not None
    assert repos.users.get(user.id) == user
    assert user.email == "kari@example.com"  # stored lower-case


def test_get_by_email_is_case_insensitive(repos, customer):
    assert repos.users.get_by_email("KUNDE@example.com ") == customer
    assert repos.users.get_by_email("nobody@example.com") is None


def test_duplicate_email_refused(repos, customer):
    with pytest.raises(DuplicateEmail):
        repos.users.add(User("kunde@example.com", "hash", "Other"))


def test_get_missing_returns_none(repos):
    assert repos.users.get(999) is None


def test_list_customers_excludes_admins(repos, customer, admin):
    assert repos.users.list_customers() == [customer]
    assert admin.role == Role.ADMIN
