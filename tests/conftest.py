import pytest

from app.models.entities import EventCategory, FoodItem, User
from app.models.enums import Allergen, Role
from app.models.repositories.factory import init_storage
from app.models.security import hash_password
from tests.factories import NEO4J_TESTS, PASSWORD, make_app


def pytest_collection_modifyitems(config, items):
    # sqlite_only: about the SQLite file itself; neo4j: needs the Neo4j test server (TEST_STORAGE=neo4j)
    for item in items:
        if NEO4J_TESTS and item.get_closest_marker("sqlite_only"):
            item.add_marker(pytest.mark.skip(reason="SQLite-specific test (TEST_STORAGE=neo4j)"))
        if not NEO4J_TESTS and item.get_closest_marker("neo4j"):
            item.add_marker(pytest.mark.skip(reason="needs a Neo4j test server (set TEST_STORAGE=neo4j)"))


@pytest.fixture
def app(tmp_path):
    """App with test settings, a temporary database and upload folder; never touches instance/."""
    return make_app(tmp_path)


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

