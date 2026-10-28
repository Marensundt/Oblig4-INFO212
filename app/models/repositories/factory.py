"""The single place that chooses the storage implementation (SQLite now, Neo4j in Oblig 5)."""
from dataclasses import dataclass

from app.models.repositories.interfaces import (
    EventCategoryRepository,
    FoodItemRepository,
    OrderRepository,
    QuestionRepository,
    UserRepository,
)


@dataclass(frozen=True)
class Repositories:
    users: UserRepository
    categories: EventCategoryRepository
    food_items: FoodItemRepository
    orders: OrderRepository
    questions: QuestionRepository


def _sqlite_database(config):
    from app.models.repositories.sqlite.database import SqliteDatabase

    return SqliteDatabase(config["DATABASE"])


def _check_storage(config):
    storage = config.get("STORAGE", "sqlite")
    if storage != "sqlite":
        raise ValueError(f"Unknown STORAGE {storage!r}")


def build_repositories(config):
    _check_storage(config)
    from app.models.repositories.sqlite.event_category_repository import SqliteEventCategoryRepository
    from app.models.repositories.sqlite.food_item_repository import SqliteFoodItemRepository
    from app.models.repositories.sqlite.order_repository import SqliteOrderRepository
    from app.models.repositories.sqlite.question_repository import SqliteQuestionRepository
    from app.models.repositories.sqlite.user_repository import SqliteUserRepository

    db = _sqlite_database(config)
    return Repositories(
        users=SqliteUserRepository(db),
        categories=SqliteEventCategoryRepository(db),
        food_items=SqliteFoodItemRepository(db),
        orders=SqliteOrderRepository(db),
        questions=SqliteQuestionRepository(db),
    )


def init_storage(config):
    """Create (or recreate) the empty storage."""
    _check_storage(config)
    _sqlite_database(config).init_schema()


def storage_is_initialised(config):
    _check_storage(config)
    return _sqlite_database(config).has_schema()
