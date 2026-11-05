"""Neo4j connection, schema and graph shape (Oblig 5; docs/plans/11). Run with TEST_STORAGE=neo4j."""
from dataclasses import replace

import pytest

from app.models.entities import EventCategory
from app.models.enums import Allergen, DietaryLabel
from app.models.errors import DataIntegrityError, StorageNotInitialised
from app.models.repositories.neo4j.database import CONSTRAINTS, Neo4jDatabase
from tests.factories import NEO4J_TEST_SETTINGS, make_order

pytestmark = pytest.mark.neo4j


@pytest.fixture
def db(repos):
    return Neo4jDatabase.from_config(NEO4J_TEST_SETTINGS)


def _count(db, query, **params):
    with db.transaction() as tx:
        return tx.run(query, **params).single()[0]


def test_has_schema_and_drop_schema(db):
    assert db.has_schema()
    db.drop_schema()
    assert not db.has_schema()
    with pytest.raises(StorageNotInitialised):
        with db.transaction():
            pass


def test_init_schema_creates_constraints_and_fixed_nodes(db):
    with db.transaction() as tx:
        names = set(tx.run("SHOW CONSTRAINTS YIELD name RETURN collect(name) AS names").single()["names"])
    assert {name for name, _, _ in CONSTRAINTS} <= names
    assert _count(db, "MATCH (a:Allergen) RETURN count(a)") == len(Allergen)
    assert _count(db, "MATCH (d:DietaryLabel) RETURN count(d)") == len(DietaryLabel)


def test_failed_unit_of_work_is_rolled_back(db, repos):
    with pytest.raises(DataIntegrityError):
        with db.transaction() as tx:
            tx.run("CREATE (:EventCategory {id: 1, slug: 'wedding', name: 'Wedding'})").consume()
            tx.run("CREATE (:EventCategory {id: 2, slug: 'wedding', name: 'Duplicate'})").consume()
    assert repos.categories.list_all() == []


def test_init_schema_resets_data(db, repos):
    repos.categories.add(EventCategory("wedding", "Wedding"))
    db.init_schema()
    assert repos.categories.list_all() == []


def test_init_schema_keeps_nodes_of_other_applications(db):
    # init-db deletes only Ekte Mat labels, so a shared Neo4j server keeps other data
    with db.transaction() as tx:
        tx.run("CREATE (:OtherApplication {name: 'keep me'})").consume()
    try:
        db.init_schema()
        assert _count(db, "MATCH (n:OtherApplication) RETURN count(n)") == 1
    finally:
        with db.transaction() as tx:
            tx.run("MATCH (n:OtherApplication) DELETE n").consume()


def test_ids_are_unique_per_label_and_never_reused(repos):
    first = repos.categories.add(EventCategory("birthday", "Birthday"))
    second = repos.categories.add(EventCategory("wedding", "Wedding"))
    assert second.id == first.id + 1


def test_food_items_and_guest_groups_share_allergen_nodes(db, repos, soup, customer):
    # The graph answers "which ordered dishes contain an allergen a guest group has?" in one pattern
    order = repos.orders.add(make_order(customer.id, soup))  # guest group allergic to nuts; soup: fish, milk
    query = (
        "MATCH (:Order {id: $id})-[:HAS_GUEST_GROUP]->(:GuestGroup)-[:ALLERGIC_TO]->(a:Allergen)"
        "<-[:CONTAINS]-(f:FoodItem)<-[:OF_ITEM]-(:OrderLine)<-[:HAS_LINE]-(:Order {id: $id})"
        " RETURN count(DISTINCT f)"
    )
    assert _count(db, query, id=order.id) == 0

    repos.food_items.update(replace(soup, allergens={Allergen.NUTS}))
    assert _count(db, query, id=order.id) == 1
    assert _count(db, "MATCH (a:Allergen {code: 'nuts'}) RETURN count(a)") == 1


def test_order_relationships(db, repos, soup, customer):
    order = repos.orders.add(make_order(customer.id, soup))
    assert _count(
        db,
        "MATCH (:User {id: $customer})-[:PLACED]->(:Order {id: $order})-[:HAS_LINE]->(:OrderLine)"
        "-[:OF_ITEM]->(:FoodItem {id: $item}) RETURN count(*)",
        customer=customer.id, order=order.id, item=soup.id,
    ) == 1
