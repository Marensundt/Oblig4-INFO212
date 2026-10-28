"""Seed script (OB4 §3: sample food items, an admin and test customers; synthetic data only; US-22)."""
import pytest

from app.models.enums import OrderStatus, PaymentStatus
from app.models.security import check_password
from app.models.seed import DEMO_PASSWORD, seed


@pytest.fixture
def seeded(repos):
    assert seed(repos) is True
    return repos


def test_seed_creates_official_minimum(seeded):
    assert len(seeded.categories.list_all()) == 6
    assert len(seeded.food_items.list_all()) == 12
    assert seeded.users.get_by_email("admin@ektemat.example").is_admin
    assert len(seeded.users.list_customers()) >= 2


def test_official_c1_categories_present(seeded):
    slugs = {c.slug for c in seeded.categories.list_all()}
    assert {"birthday", "confirmation", "wedding", "conference", "julebord"} <= slugs


def test_every_official_status_is_represented(seeded):
    orders = seeded.orders.list()
    assert {o.status for o in orders} == set(OrderStatus)
    assert {o.payment_status for o in orders} == set(PaymentStatus)


def test_orders_have_guest_groups_and_lines(seeded):
    for order in seeded.orders.list():
        assert order.lines and order.guest_groups
        assert order.total_nok > 0


def test_unpublished_item_not_on_menu(seeded):
    published = {item.name for _, items in seeded.food_items.list_published_by_category() for item in items}
    assert "Rakfisk tasting" not in published
    assert "Kids menu" in published


def test_questions_answered_and_unanswered(seeded):
    questions = seeded.questions.list_all()
    assert len(questions) == 3
    assert sum(q.is_answered for q in questions) == 1


def test_seed_is_idempotent(seeded):
    assert seed(seeded) is False
    assert len(seeded.food_items.list_all()) == 12
    assert len(seeded.orders.list()) == 6


def test_synthetic_accounts_with_hashed_demo_password(seeded):
    users = [seeded.users.get_by_email("admin@ektemat.example"), *seeded.users.list_customers()]
    for user in users:
        assert user.email.endswith((".example", "@example.com"))
        assert user.password_hash != DEMO_PASSWORD
        assert check_password(user.password_hash, DEMO_PASSWORD)
