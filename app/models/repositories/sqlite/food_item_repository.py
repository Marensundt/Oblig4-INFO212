from app.models.entities import FoodItem
from app.models.enums import Allergen, DietaryLabel
from app.models.errors import NotFound
from app.models.repositories.interfaces import FoodItemRepository
from app.models.repositories.sqlite.event_category_repository import _to_category


def _placeholders(values):
    return ", ".join("?" for _ in values)


class SqliteFoodItemRepository(FoodItemRepository):
    def __init__(self, db):
        self.db = db

    def add(self, item):
        with self.db.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO food_items (name, description, price_nok, min_order_qty, published, image_filename)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (item.name, item.description, item.price_nok, item.min_order_qty,
                 int(item.published), item.image_filename),
            )
            item_id = cursor.lastrowid
            self._save_relations(conn, item_id, item)
        return self.get(item_id)

    def update(self, item):
        with self.db.connect() as conn:
            cursor = conn.execute(
                "UPDATE food_items SET name = ?, description = ?, price_nok = ?, min_order_qty = ?,"
                " published = ?, image_filename = ? WHERE id = ?",
                (item.name, item.description, item.price_nok, item.min_order_qty,
                 int(item.published), item.image_filename, item.id),
            )
            if cursor.rowcount == 0:
                raise NotFound(f"Food item {item.id}")
            for table in ("food_item_categories", "food_item_allergens", "food_item_dietary_labels"):
                conn.execute(f"DELETE FROM {table} WHERE food_item_id = ?", (item.id,))
            self._save_relations(conn, item.id, item)
        return self.get(item.id)

    def delete(self, item_id):
        with self.db.connect() as conn:
            cursor = conn.execute("DELETE FROM food_items WHERE id = ?", (item_id,))
            if cursor.rowcount == 0:
                raise NotFound(f"Food item {item_id}")

    def get(self, item_id):
        items = self.get_many([item_id])
        return items[0] if items else None

    def get_many(self, item_ids):
        item_ids = list(item_ids)
        if not item_ids:
            return []
        with self.db.connect() as conn:
            return self._load(conn, f"WHERE id IN ({_placeholders(item_ids)}) ORDER BY name", item_ids)

    def list_all(self):
        with self.db.connect() as conn:
            return self._load(conn, "ORDER BY name", [])

    def list_published_by_category(self):
        with self.db.connect() as conn:
            items = {item.id: item for item in self._load(conn, "WHERE published = 1 ORDER BY name", [])}
            categories = conn.execute("SELECT * FROM event_categories ORDER BY sort_order, name").fetchall()
        result = []
        for row in categories:
            members = [item for item in items.values() if row["id"] in item.category_ids]
            if members:
                result.append((_to_category(row), members))
        return result

    def is_used_in_orders(self, item_id):
        with self.db.connect() as conn:
            row = conn.execute("SELECT 1 FROM order_lines WHERE food_item_id = ? LIMIT 1", (item_id,)).fetchone()
        return row is not None

    def _save_relations(self, conn, item_id, item):
        conn.executemany(
            "INSERT INTO food_item_categories (food_item_id, category_id) VALUES (?, ?)",
            [(item_id, category_id) for category_id in item.category_ids],
        )
        conn.executemany(
            "INSERT INTO food_item_allergens (food_item_id, allergen) VALUES (?, ?)",
            [(item_id, Allergen(a).value) for a in item.allergens],
        )
        conn.executemany(
            "INSERT INTO food_item_dietary_labels (food_item_id, label) VALUES (?, ?)",
            [(item_id, DietaryLabel(label).value) for label in item.dietary_labels],
        )

    def _load(self, conn, where_clause, params):
        rows = conn.execute(f"SELECT * FROM food_items {where_clause}", params).fetchall()
        if not rows:
            return []
        ids = [row["id"] for row in rows]
        in_ids = f"food_item_id IN ({_placeholders(ids)})"
        categories, allergens, labels = {}, {}, {}
        for r in conn.execute(
            f"SELECT food_item_id, category_id FROM food_item_categories WHERE {in_ids} ORDER BY category_id", ids
        ):
            categories.setdefault(r[0], []).append(r[1])
        for r in conn.execute(f"SELECT food_item_id, allergen FROM food_item_allergens WHERE {in_ids}", ids):
            allergens.setdefault(r[0], set()).add(Allergen(r[1]))
        for r in conn.execute(f"SELECT food_item_id, label FROM food_item_dietary_labels WHERE {in_ids}", ids):
            labels.setdefault(r[0], set()).add(DietaryLabel(r[1]))
        return [
            FoodItem(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                price_nok=row["price_nok"],
                min_order_qty=row["min_order_qty"],
                category_ids=categories.get(row["id"], []),
                allergens=allergens.get(row["id"], set()),
                dietary_labels=labels.get(row["id"], set()),
                published=bool(row["published"]),
                image_filename=row["image_filename"],
            )
            for row in rows
        ]
