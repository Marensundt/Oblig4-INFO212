from app.models.entities import FoodItem
from app.models.enums import Allergen, DietaryLabel
from app.models.errors import DataIntegrityError, NotFound
from app.models.repositories.interfaces import FoodItemRepository
from app.models.repositories.neo4j.database import check, next_ids
from app.models.repositories.neo4j.event_category_repository import _to_category

# The relationships of a food item, read together with the node
_LOAD = (
    " RETURN f,"
    " [(f)-[:IN_CATEGORY]->(c:EventCategory) | c.id] AS category_ids,"
    " [(f)-[:CONTAINS]->(a:Allergen) | a.code] AS allergens,"
    " [(f)-[:HAS_LABEL]->(d:DietaryLabel) | d.code] AS labels"
    " ORDER BY f.name, f.id"
)


def _properties(item):
    check(item.price_nok > 0, "price_nok must be > 0")  # DV-03 (ASSUMPTION)
    check(item.min_order_qty >= 1, "min_order_qty must be >= 1")  # needed for C2 (OFFICIAL)
    return {
        "name": item.name,
        "description": item.description,
        "price_nok": item.price_nok,
        "min_order_qty": item.min_order_qty,
        "published": bool(item.published),
        "image_filename": item.image_filename,
    }


def _to_food_item(record):
    node = record["f"]
    return FoodItem(
        id=node["id"],
        name=node["name"],
        description=node["description"],
        price_nok=node["price_nok"],
        min_order_qty=node["min_order_qty"],
        category_ids=sorted(record["category_ids"]),
        allergens={Allergen(code) for code in record["allergens"]},
        dietary_labels={DietaryLabel(code) for code in record["labels"]},
        published=node["published"],
        image_filename=node.get("image_filename"),
    )


class Neo4jFoodItemRepository(FoodItemRepository):
    def __init__(self, db):
        self.db = db

    def add(self, item):
        properties = _properties(item)
        with self.db.transaction() as tx:
            [item_id] = next_ids(tx, "FoodItem")
            tx.run("CREATE (f:FoodItem $properties) SET f.id = $id", properties=properties, id=item_id).consume()
            self._save_relations(tx, item_id, item)
        return self.get(item_id)

    def update(self, item):
        properties = _properties(item)
        with self.db.transaction() as tx:
            record = tx.run(
                "MATCH (f:FoodItem {id: $id}) SET f += $properties"
                " WITH f OPTIONAL MATCH (f)-[r:IN_CATEGORY|CONTAINS|HAS_LABEL]->() DELETE r"
                " RETURN count(DISTINCT f) AS found",
                id=item.id, properties=properties,
            ).single()
            if record["found"] == 0:
                raise NotFound(f"Food item {item.id}")
            self._save_relations(tx, item.id, item)
        return self.get(item.id)

    def delete(self, item_id):
        # DETACH also removes OF_ITEM from order lines, which keep name and price (like ON DELETE SET NULL)
        with self.db.transaction() as tx:
            record = tx.run(
                "MATCH (f:FoodItem {id: $id}) DETACH DELETE f RETURN count(*) AS deleted", id=item_id
            ).single()
            if record["deleted"] == 0:
                raise NotFound(f"Food item {item_id}")

    def get(self, item_id):
        items = self.get_many([item_id])
        return items[0] if items else None

    def get_many(self, item_ids):
        item_ids = list(item_ids)
        if not item_ids:
            return []
        with self.db.transaction() as tx:
            return self._load(tx, "MATCH (f:FoodItem) WHERE f.id IN $ids", ids=item_ids)

    def list_all(self):
        with self.db.transaction() as tx:
            return self._load(tx, "MATCH (f:FoodItem)")

    def list_published_by_category(self):
        with self.db.transaction() as tx:
            items = self._load(tx, "MATCH (f:FoodItem {published: true})")
            categories = [_to_category(record["c"]) for record in
                          tx.run("MATCH (c:EventCategory) RETURN c ORDER BY c.sort_order, c.name")]
        result = []
        for category in categories:
            members = [item for item in items if category.id in item.category_ids]
            if members:
                result.append((category, members))
        return result

    def is_used_in_orders(self, item_id):
        with self.db.transaction() as tx:
            record = tx.run(
                "RETURN EXISTS { MATCH (:OrderLine)-[:OF_ITEM]->(:FoodItem {id: $id}) } AS used", id=item_id
            ).single()
        return record["used"]

    def _save_relations(self, tx, item_id, item):
        category_ids = list(item.category_ids)
        allergens = [Allergen(a).value for a in item.allergens]
        labels = [DietaryLabel(label).value for label in item.dietary_labels]
        record = tx.run(
            "MATCH (f:FoodItem {id: $id})"
            " CALL (f) { UNWIND $category_ids AS category_id MATCH (c:EventCategory {id: category_id})"
            "   CREATE (f)-[:IN_CATEGORY]->(c) RETURN count(c) AS categories }"
            " CALL (f) { UNWIND $allergens AS code MATCH (a:Allergen {code: code})"
            "   CREATE (f)-[:CONTAINS]->(a) RETURN count(a) AS allergens }"
            " CALL (f) { UNWIND $labels AS code MATCH (d:DietaryLabel {code: code})"
            "   CREATE (f)-[:HAS_LABEL]->(d) RETURN count(d) AS labels }"
            " RETURN categories, allergens, labels",
            id=item_id, category_ids=category_ids, allergens=allergens, labels=labels,
        ).single()
        # A reference to a missing category is refused, like a foreign key in SQLite
        if (record["categories"], record["allergens"], record["labels"]) != (
                len(set(category_ids)), len(allergens), len(labels)):
            raise DataIntegrityError(f"Food item {item_id} refers to a category, allergen or label that does not exist")

    def _load(self, tx, match, **params):
        return [_to_food_item(record) for record in tx.run(match + _LOAD, **params)]
