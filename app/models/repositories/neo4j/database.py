"""Neo4j connection for the repositories (Oblig 5). Only code in this package uses the Neo4j driver.

Graph model and constraints: docs/plans/11-oblig5-neo4j.md. All Cypher is parameterised (`$name`).
"""
import atexit
from contextlib import contextmanager
from datetime import datetime

from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ConstraintError, ServiceUnavailable, SessionExpired

from app.models.enums import Allergen, DietaryLabel
from app.models.errors import DataIntegrityError, StorageNotInitialised, StorageUnavailable

# Every label this application stores; init_schema() deletes only nodes with these labels.
LABELS = ["User", "EventCategory", "FoodItem", "Allergen", "DietaryLabel", "Order", "OrderLine",
          "GuestGroup", "Question", "Counter", "EkteMatSchema"]

# (constraint name, label, property): all unique
CONSTRAINTS = [
    ("ektemat_user_id", "User", "id"),
    ("ektemat_user_email", "User", "email"),
    ("ektemat_category_id", "EventCategory", "id"),
    ("ektemat_category_slug", "EventCategory", "slug"),
    ("ektemat_food_item_id", "FoodItem", "id"),
    ("ektemat_allergen_code", "Allergen", "code"),
    ("ektemat_dietary_label_code", "DietaryLabel", "code"),
    ("ektemat_order_id", "Order", "id"),
    ("ektemat_order_number", "Order", "order_number"),
    ("ektemat_order_line_id", "OrderLine", "id"),
    ("ektemat_guest_group_id", "GuestGroup", "id"),
    ("ektemat_question_id", "Question", "id"),
    ("ektemat_counter_name", "Counter", "name"),
]

SCHEMA_VERSION = 1

# One driver (connection pool) per server and user, shared by all app instances in this process.
_drivers = {}


def _driver(uri, user, password):
    key = (uri, user, password)
    if key not in _drivers:
        auth = (user, password) if password else None  # no password: server started with NEO4J_AUTH=none
        _drivers[key] = GraphDatabase.driver(uri, auth=auth, connection_timeout=5)
    return _drivers[key]


@atexit.register
def _close_drivers():
    for driver in _drivers.values():
        driver.close()
    _drivers.clear()


def now():
    # Whole seconds, like the SQLite implementation
    return datetime.now().replace(microsecond=0)


def to_native(value):
    """Neo4j temporal value (Date, DateTime) -> Python date/datetime; None stays None."""
    return value.to_native() if value is not None else None


def check(condition, message):
    """Value rules that SQLite enforces with CHECK constraints (Community Edition has no value constraints)."""
    if not condition:
        raise DataIntegrityError(message)


def next_ids(tx, name, count=1):
    """Reserve `count` consecutive integer ids from the counter `name` in the current transaction."""
    if count == 0:
        return []
    record = tx.run(
        "MERGE (c:Counter {name: $name}) ON CREATE SET c.value = 0 "
        "SET c.value = c.value + $count RETURN c.value AS last",
        name=name, count=count,
    ).single()
    last = record["last"]
    return list(range(last - count + 1, last + 1))


class Neo4jDatabase:
    """One transaction per unit of work: commit on success, rollback on error."""

    def __init__(self, uri, user, password, database):
        self.uri = uri
        self.user = user
        self._password = password
        self.database = database
        self._ready = False  # cached once the schema marker has been seen

    @classmethod
    def from_config(cls, config):
        return cls(config["NEO4J_URI"], config["NEO4J_USER"], config["NEO4J_PASSWORD"], config["NEO4J_DATABASE"])

    def __repr__(self):
        return f"Neo4j database {self.database!r} at {self.uri}"

    @contextmanager
    def _errors(self):
        """Translate driver errors into domain errors, so none leave the model layer."""
        try:
            yield
        except ConstraintError as error:
            raise DataIntegrityError(error.message) from error
        except AuthError as error:
            raise StorageUnavailable(f"Neo4j refused the login for user {self.user!r} at {self.uri}") from error
        except (ServiceUnavailable, SessionExpired) as error:
            raise StorageUnavailable(f"Cannot reach Neo4j at {self.uri}") from error

    def _session(self):
        return _driver(self.uri, self.user, self._password).session(database=self.database)

    @contextmanager
    def transaction(self):
        with self._errors():
            self._check_ready()
            with self._session() as session, session.begin_transaction() as tx:
                yield tx
                tx.commit()  # leaving the block without commit (on an error) rolls back

    def _check_ready(self):
        if not self._ready:
            self._ready = self.has_schema()
        if not self._ready:
            raise StorageNotInitialised(f"{self} has no Ekte Mat schema")

    def has_schema(self):
        with self._errors(), self._session() as session:
            record = session.run(
                "MATCH (s:EkteMatSchema {version: $version}) RETURN count(s) > 0 AS found", version=SCHEMA_VERSION
            ).single()
        return record["found"]

    def init_schema(self):
        """Delete all Ekte Mat data and recreate constraints and the fixed allergen and label nodes."""
        with self._errors(), self._session() as session:
            self._delete_data(session)
            for name, label, prop in CONSTRAINTS:
                # Schema commands cannot take parameters; names come from the fixed list above.
                session.run(f"CREATE CONSTRAINT {name} IF NOT EXISTS FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE")
            session.run(
                "UNWIND $allergens AS code CREATE (:Allergen {code: code}) "
                "WITH count(*) AS created UNWIND $labels AS code CREATE (:DietaryLabel {code: code})",
                allergens=[a.value for a in Allergen], labels=[d.value for d in DietaryLabel],
            ).consume()
            session.run("CREATE (:EkteMatSchema {version: $version})", version=SCHEMA_VERSION).consume()
        self._ready = True

    def drop_schema(self):
        """Delete all Ekte Mat data and constraints (an empty, uninitialised database; used by tests)."""
        with self._errors(), self._session() as session:
            self._delete_data(session)
            for name, _, _ in CONSTRAINTS:
                session.run(f"DROP CONSTRAINT {name} IF EXISTS").consume()
        self._ready = False

    @staticmethod
    def _delete_data(session):
        session.run(
            "MATCH (n) WHERE any(label IN labels(n) WHERE label IN $labels) DETACH DELETE n", labels=LABELS
        ).consume()
