from app.models.entities import EventCategory
from app.models.repositories.interfaces import EventCategoryRepository


def _to_category(row):
    return EventCategory(id=row["id"], slug=row["slug"], name=row["name"], sort_order=row["sort_order"])


class SqliteEventCategoryRepository(EventCategoryRepository):
    def __init__(self, db):
        self.db = db

    def add(self, category):
        with self.db.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO event_categories (slug, name, sort_order) VALUES (?, ?, ?)",
                (category.slug, category.name, category.sort_order),
            )
        return EventCategory(category.slug, category.name, category.sort_order, id=cursor.lastrowid)

    def list_all(self):
        with self.db.connect() as conn:
            rows = conn.execute("SELECT * FROM event_categories ORDER BY sort_order, name").fetchall()
        return [_to_category(row) for row in rows]

    def get_by_slug(self, slug):
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM event_categories WHERE slug = ?", (slug,)).fetchone()
        return _to_category(row) if row else None
