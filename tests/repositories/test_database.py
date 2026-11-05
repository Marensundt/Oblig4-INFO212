import pytest

from app.models.enums import Allergen, DietaryLabel
from app.models.errors import DataIntegrityError
from app.models.repositories.sqlite.database import SqliteDatabase

pytestmark = pytest.mark.sqlite_only


@pytest.fixture
def db(tmp_path):
    database = SqliteDatabase(tmp_path / "test.sqlite")
    database.init_schema()
    return database


def test_has_schema(tmp_path, db):
    assert db.has_schema()
    assert not SqliteDatabase(tmp_path / "missing.sqlite").has_schema()


def test_foreign_keys_are_enforced(db):
    with pytest.raises(DataIntegrityError):
        with db.connect() as conn:
            conn.execute("INSERT INTO food_item_categories (food_item_id, category_id) VALUES (99, 99)")


def test_failed_unit_of_work_is_rolled_back(db):
    with pytest.raises(DataIntegrityError):
        with db.connect() as conn:
            conn.execute("INSERT INTO event_categories (slug, name) VALUES ('wedding', 'Wedding')")
            conn.execute("INSERT INTO event_categories (slug, name) VALUES ('wedding', 'Duplicate')")
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM event_categories").fetchone()[0] == 0


def test_schema_accepts_every_enum_value(db):
    # The CHECK lists in schema.sql must match the enums in app/models/enums.py
    with db.connect() as conn:
        conn.execute("INSERT INTO food_items (name, price_nok, min_order_qty) VALUES ('X', 100, 1)")
        for allergen in Allergen:
            conn.execute("INSERT INTO food_item_allergens VALUES (1, ?)", (allergen.value,))
        for label in DietaryLabel:
            conn.execute("INSERT INTO food_item_dietary_labels VALUES (1, ?)", (label.value,))


def test_init_schema_resets_data(db):
    with db.connect() as conn:
        conn.execute("INSERT INTO event_categories (slug, name) VALUES ('wedding', 'Wedding')")
    db.init_schema()
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM event_categories").fetchone()[0] == 0
