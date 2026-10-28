"""File-based SQLite: data survives an application restart (decision 2026-10-28)."""
from app import create_app
from app.models.repositories.factory import init_storage
from app.models.seed import seed
from config import TestConfig


def test_data_survives_restart(tmp_path):
    overrides = {"DATABASE": str(tmp_path / "ektemat.sqlite")}

    first = create_app(TestConfig, overrides=overrides)
    init_storage(first.config)
    seed(first.repos)
    order = first.repos.orders.list()[0]

    restarted = create_app(TestConfig, overrides=overrides)
    assert len(restarted.repos.food_items.list_all()) == 12
    assert restarted.repos.orders.get(order.id) == order
