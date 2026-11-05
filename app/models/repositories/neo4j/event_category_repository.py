from app.models.entities import EventCategory
from app.models.repositories.interfaces import EventCategoryRepository
from app.models.repositories.neo4j.database import next_ids


def _to_category(node):
    return EventCategory(id=node["id"], slug=node["slug"], name=node["name"], sort_order=node["sort_order"])


class Neo4jEventCategoryRepository(EventCategoryRepository):
    def __init__(self, db):
        self.db = db

    def add(self, category):
        with self.db.transaction() as tx:
            [category_id] = next_ids(tx, "EventCategory")
            tx.run(
                "CREATE (:EventCategory {id: $id, slug: $slug, name: $name, sort_order: $sort_order})",
                id=category_id, slug=category.slug, name=category.name, sort_order=category.sort_order,
            ).consume()
        return EventCategory(category.slug, category.name, category.sort_order, id=category_id)

    def list_all(self):
        with self.db.transaction() as tx:
            records = list(tx.run("MATCH (c:EventCategory) RETURN c ORDER BY c.sort_order, c.name"))
        return [_to_category(record["c"]) for record in records]

    def get_by_slug(self, slug):
        with self.db.transaction() as tx:
            record = tx.run("MATCH (c:EventCategory {slug: $slug}) RETURN c", slug=slug).single()
        return _to_category(record["c"]) if record else None
