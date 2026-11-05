"""Data survives an application restart: SQLite file (decision 2026-10-28) or Neo4j server (Oblig 5)."""
from app.models.repositories.factory import init_storage
from app.models.seed import seed
from tests.factories import make_app


def test_data_survives_restart(tmp_path):
    first = make_app(tmp_path, database_name="ektemat.sqlite")
    init_storage(first.config)
    seed(first.repos)
    order = first.repos.orders.list()[0]

    restarted = make_app(tmp_path, database_name="ektemat.sqlite", empty=False)
    assert len(restarted.repos.food_items.list_all()) == 12
    assert restarted.repos.orders.get(order.id) == order
