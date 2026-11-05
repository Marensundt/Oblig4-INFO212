"""Helpers for building test data and test apps."""
import os
from datetime import date, timedelta

from app import create_app
from app.models.entities import GuestGroup, Order, OrderLine
from app.models.enums import Allergen
from config import TestConfig

PASSWORD = "test-password"  # password of the customer/admin fixtures

# `TEST_STORAGE=neo4j pytest` runs the suite against Neo4j (Oblig 5). The test server has its own settings,
# so a test run never uses the NEO4J_* development database from .env. Every test wipes the test database.
NEO4J_TESTS = os.environ.get("TEST_STORAGE", "sqlite").strip().lower() == "neo4j"
NEO4J_TEST_SETTINGS = {
    "STORAGE": "neo4j",
    "NEO4J_URI": os.environ.get("NEO4J_TEST_URI", "bolt://localhost:7687"),
    "NEO4J_USER": os.environ.get("NEO4J_TEST_USER", "neo4j"),
    "NEO4J_PASSWORD": os.environ.get("NEO4J_TEST_PASSWORD", ""),
    "NEO4J_DATABASE": os.environ.get("NEO4J_TEST_DATABASE", "neo4j"),
}


def make_app(tmp_path, config_class=TestConfig, database_name="test.sqlite", empty=True, **overrides):
    """App with test settings, a temporary upload folder and a temporary SQLite file or the Neo4j test database.

    With `empty` the Neo4j test database starts without data or schema, like a new SQLite file.
    """
    settings = {"DATABASE": str(tmp_path / database_name), "UPLOAD_FOLDER": str(tmp_path / "uploads")}
    if NEO4J_TESTS:
        settings.update(NEO4J_TEST_SETTINGS)
        if empty:
            from app.models.repositories.neo4j.database import Neo4jDatabase

            Neo4jDatabase.from_config(NEO4J_TEST_SETTINGS).drop_schema()
    settings.update(overrides)
    return create_app(config_class, overrides=settings)


def log_in(client, email, password, next_url=""):
    return client.post("/account/login", data={"email": email, "password": password, "next": next_url})


def make_order(customer_id, food_item, days_ahead=30, guests=20, **kwargs):
    return Order(
        customer_id=customer_id,
        event_date=date.today() + timedelta(days=days_ahead),
        guest_count=guests,
        delivery_address="Bryggen 1, 5003 Bergen",
        lines=[OrderLine(food_item.name, food_item.price_nok, guests, food_item_id=food_item.id)],
        guest_groups=[GuestGroup("Adults", guests, {Allergen.NUTS}, "1 vegetarian")],
        **kwargs,
    )
