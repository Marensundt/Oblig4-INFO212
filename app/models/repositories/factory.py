"""The single place that chooses the storage implementation: Neo4j (default, Oblig 5) or SQLite.

Set STORAGE=sqlite (environment or .env) to use SQLite; see config.py for the connection settings.
"""
from dataclasses import dataclass

from app.models.repositories.interfaces import (
    EventCategoryRepository,
    FoodItemRepository,
    OrderRepository,
    QuestionRepository,
    UserRepository,
)

STORAGES = ("neo4j", "sqlite")
DEFAULT_STORAGE = "neo4j"


@dataclass(frozen=True)
class Repositories:
    users: UserRepository
    categories: EventCategoryRepository
    food_items: FoodItemRepository
    orders: OrderRepository
    questions: QuestionRepository


def _storage(config):
    storage = config.get("STORAGE") or DEFAULT_STORAGE
    if storage not in STORAGES:
        raise ValueError(f"Unknown STORAGE {storage!r} (expected one of {', '.join(STORAGES)})")
    return storage


def _database(config):
    if _storage(config) == "neo4j":
        from app.models.repositories.neo4j.database import Neo4jDatabase

        return Neo4jDatabase.from_config(config)
    from app.models.repositories.sqlite.database import SqliteDatabase

    return SqliteDatabase(config["DATABASE"])


def _sqlite_repositories(db):
    from app.models.repositories.sqlite.event_category_repository import SqliteEventCategoryRepository
    from app.models.repositories.sqlite.food_item_repository import SqliteFoodItemRepository
    from app.models.repositories.sqlite.order_repository import SqliteOrderRepository
    from app.models.repositories.sqlite.question_repository import SqliteQuestionRepository
    from app.models.repositories.sqlite.user_repository import SqliteUserRepository

    return Repositories(
        users=SqliteUserRepository(db),
        categories=SqliteEventCategoryRepository(db),
        food_items=SqliteFoodItemRepository(db),
        orders=SqliteOrderRepository(db),
        questions=SqliteQuestionRepository(db),
    )


def _neo4j_repositories(db):
    from app.models.repositories.neo4j.event_category_repository import Neo4jEventCategoryRepository
    from app.models.repositories.neo4j.food_item_repository import Neo4jFoodItemRepository
    from app.models.repositories.neo4j.order_repository import Neo4jOrderRepository
    from app.models.repositories.neo4j.question_repository import Neo4jQuestionRepository
    from app.models.repositories.neo4j.user_repository import Neo4jUserRepository

    return Repositories(
        users=Neo4jUserRepository(db),
        categories=Neo4jEventCategoryRepository(db),
        food_items=Neo4jFoodItemRepository(db),
        orders=Neo4jOrderRepository(db),
        questions=Neo4jQuestionRepository(db),
    )


def build_repositories(config):
    db = _database(config)
    if _storage(config) == "neo4j":
        return _neo4j_repositories(db)
    return _sqlite_repositories(db)


def init_storage(config):
    """Create (or recreate) the empty storage."""
    _database(config).init_schema()


def storage_is_initialised(config):
    return _database(config).has_schema()


def describe_storage(config):
    """Where the data is stored, for messages (never includes a password)."""
    if _storage(config) == "neo4j":
        return f"Neo4j database {config['NEO4J_DATABASE']!r} at {config['NEO4J_URI']}"
    return config["DATABASE"]
