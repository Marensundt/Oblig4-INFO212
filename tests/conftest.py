import pytest

from app import create_app
from app.models.entities import EventCategory, FoodItem, User
from app.models.enums import Allergen, Role
from app.models.repositories.factory import init_storage
from app.models.security import hash_password
from config import TestConfig
from tests.factories import PASSWORD


@pytest.fixture
def app(tmp_path):
    """App with test settings and a temporary database path; never touches instance/."""
    return create_app(TestConfig, overrides={"DATABASE": str(tmp_path / "test.sqlite")})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def repos(app):
    """Repositories on a fresh, empty temporary database."""
    init_storage(app.config)
    return app.repos


@pytest.fixture
def customer(repos):
    return repos.users.add(User("kunde@example.com", hash_password(PASSWORD), "Test Kunde"))


@pytest.fixture
def admin(repos):
    return repos.users.add(User("admin@example.com", hash_password(PASSWORD), "Test Admin", role=Role.ADMIN))


@pytest.fixture
def categories(repos):
    return {
        slug: repos.categories.add(EventCategory(slug, slug.capitalize(), sort_order))
        for sort_order, slug in enumerate(["birthday", "wedding", "conference"])
    }


@pytest.fixture
def soup(repos, categories):
    return repos.food_items.add(FoodItem(
        "Fish soup", "Bergen cod", 189, 10,
        category_ids=[categories["conference"].id], allergens={Allergen.FISH, Allergen.MILK}, published=True,
    ))

