from datetime import date

from app.models.entities import GuestGroup, Order, OrderLine
from app.models.enums import Allergen, OrderStatus, PaymentStatus
from app.models.errors import DataIntegrityError, InvalidStatusTransition, NotFound
from app.models.repositories.interfaces import OrderRepository
from app.models.repositories.neo4j.database import check, next_ids, now, to_native

# An order with its customer, lines (and the food item each refers to) and guest groups (with allergies)
_LOAD = (
    " MATCH (customer:User)-[:PLACED]->(o)"
    " RETURN o, customer.id AS customer_id,"
    " [(o)-[:HAS_LINE]->(l:OrderLine) | {line: l, food_item_id: [(l)-[:OF_ITEM]->(f:FoodItem) | f.id][0]}] AS lines,"
    " [(o)-[:HAS_GUEST_GROUP]->(g:GuestGroup) | {group: g, allergies: [(g)-[:ALLERGIC_TO]->(a:Allergen) | a.code]}]"
    "   AS groups"
    " ORDER BY o.event_date, o.id"
)


def _check_order(order):
    check(order.guest_count >= 1, "guest_count must be >= 1")  # DV-01 (ASSUMPTION)
    for line in order.lines:
        check(line.unit_price_nok > 0, "unit_price_nok must be > 0")
        check(line.quantity >= 1, "quantity must be >= 1")
    for group in order.guest_groups:
        check(group.count >= 1, "guest group count must be >= 1")


def _to_order(record):
    node = record["o"]
    lines = sorted(
        (OrderLine(id=entry["line"]["id"], food_item_id=entry["food_item_id"], item_name=entry["line"]["item_name"],
                   unit_price_nok=entry["line"]["unit_price_nok"], quantity=entry["line"]["quantity"])
         for entry in record["lines"]),
        key=lambda line: line.id,
    )
    groups = sorted(
        (GuestGroup(id=entry["group"]["id"], label=entry["group"]["label"], count=entry["group"]["count"],
                    dietary_notes=entry["group"]["dietary_notes"],
                    allergies={Allergen(code) for code in entry["allergies"]})
         for entry in record["groups"]),
        key=lambda group: group.id,
    )
    return Order(
        id=node["id"],
        order_number=node["order_number"],
        customer_id=record["customer_id"],
        event_date=to_native(node["event_date"]),
        guest_count=node["guest_count"],
        delivery_address=node["delivery_address"],
        status=OrderStatus(node["status"]),
        payment_status=PaymentStatus(node["payment_status"]),
        created_at=to_native(node["created_at"]),
        updated_at=to_native(node["updated_at"]),
        lines=lines,
        guest_groups=groups,
    )


class Neo4jOrderRepository(OrderRepository):
    def __init__(self, db):
        self.db = db

    def add(self, order):
        _check_order(order)
        status = OrderStatus(order.status).value
        payment_status = PaymentStatus(order.payment_status).value
        created_at = now()
        with self.db.transaction() as tx:
            [order_id] = next_ids(tx, "Order")
            # The counter node is locked until commit, so two orders never get the same number
            [number] = next_ids(tx, f"order_number:{date.today():%y}")
            record = tx.run(
                "MATCH (customer:User {id: $customer_id})"
                " CREATE (customer)-[:PLACED]->(o:Order {id: $id, order_number: $order_number,"
                " event_date: $event_date, guest_count: $guest_count, delivery_address: $delivery_address,"
                " status: $status, payment_status: $payment_status, created_at: $created_at, updated_at: $created_at})"
                " RETURN o.id AS id",
                customer_id=order.customer_id, id=order_id, order_number=f"{date.today():%y}-{number:04d}",
                event_date=order.event_date, guest_count=order.guest_count,
                delivery_address=order.delivery_address, status=status, payment_status=payment_status,
                created_at=created_at,
            ).single()
            if record is None:
                raise DataIntegrityError(f"Customer {order.customer_id} does not exist")
            self._add_lines(tx, order_id, order.lines)
            self._add_guest_groups(tx, order_id, order.guest_groups)
        return self.get(order_id)

    def get(self, order_id):
        with self.db.transaction() as tx:
            orders = self._load(tx, "MATCH (o:Order {id: $id})", id=order_id)
        return orders[0] if orders else None

    def list(self, status=None, date_from=None, date_to=None):
        conditions, params = [], {}
        if status is not None:
            conditions.append("o.status = $status")
            params["status"] = OrderStatus(status).value
        if date_from is not None:
            conditions.append("o.event_date >= $date_from")
            params["date_from"] = date_from
        if date_to is not None:
            conditions.append("o.event_date <= $date_to")
            params["date_to"] = date_to
        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        with self.db.transaction() as tx:
            return self._load(tx, "MATCH (o:Order)" + where, **params)

    def list_for_customer(self, customer_id):
        with self.db.transaction() as tx:
            return self._load(tx, "MATCH (:User {id: $customer_id})-[:PLACED]->(o:Order)", customer_id=customer_id)

    def update_status(self, order_id, new_status):
        new_status = OrderStatus(new_status)
        with self.db.transaction() as tx:
            # Setting updated_at first takes the write lock, so the check below sees the current status
            record = tx.run(
                "MATCH (o:Order {id: $id}) SET o.updated_at = $updated_at RETURN o.status AS status",
                id=order_id, updated_at=now(),
            ).single()
            if record is None:
                raise NotFound(f"Order {order_id}")
            current = OrderStatus(record["status"])
            if not current.can_change_to(new_status):
                raise InvalidStatusTransition(current, new_status)  # rolls back updated_at
            tx.run("MATCH (o:Order {id: $id}) SET o.status = $status", id=order_id, status=new_status.value).consume()
        return self.get(order_id)

    def update_payment_status(self, order_id, payment_status):
        payment_status = PaymentStatus(payment_status)
        with self.db.transaction() as tx:
            record = tx.run(
                "MATCH (o:Order {id: $id}) SET o.payment_status = $payment_status, o.updated_at = $updated_at"
                " RETURN o.id AS id",
                id=order_id, payment_status=payment_status.value, updated_at=now(),
            ).single()
            if record is None:
                raise NotFound(f"Order {order_id}")
        return self.get(order_id)

    def _add_lines(self, tx, order_id, lines):
        ids = next_ids(tx, "OrderLine", len(lines))
        rows = [{"id": line_id, "food_item_id": line.food_item_id, "item_name": line.item_name,
                 "unit_price_nok": line.unit_price_nok, "quantity": line.quantity}
                for line_id, line in zip(ids, lines)]
        record = tx.run(
            "MATCH (o:Order {id: $order_id})"
            " UNWIND $rows AS row"
            " CREATE (o)-[:HAS_LINE]->(l:OrderLine {id: row.id, item_name: row.item_name,"
            " unit_price_nok: row.unit_price_nok, quantity: row.quantity})"
            " WITH l, row WHERE row.food_item_id IS NOT NULL"
            " MATCH (f:FoodItem {id: row.food_item_id})"
            " CREATE (l)-[:OF_ITEM]->(f)"
            " RETURN count(f) AS linked",
            order_id=order_id, rows=rows,
        ).single()
        # A line that refers to a missing food item is refused, like a foreign key in SQLite
        if record["linked"] != sum(line.food_item_id is not None for line in lines):
            raise DataIntegrityError(f"Order {order_id} refers to a food item that does not exist")

    def _add_guest_groups(self, tx, order_id, groups):
        ids = next_ids(tx, "GuestGroup", len(groups))
        rows = [{"id": group_id, "label": group.label, "count": group.count, "dietary_notes": group.dietary_notes,
                 "allergies": [Allergen(a).value for a in group.allergies]}
                for group_id, group in zip(ids, groups)]
        tx.run(
            "MATCH (o:Order {id: $order_id})"
            " UNWIND $rows AS row"
            " CREATE (o)-[:HAS_GUEST_GROUP]->(g:GuestGroup {id: row.id, label: row.label, count: row.count,"
            " dietary_notes: row.dietary_notes})"
            " WITH g, row UNWIND row.allergies AS code"
            " MATCH (a:Allergen {code: code})"
            " CREATE (g)-[:ALLERGIC_TO]->(a)",
            order_id=order_id, rows=rows,
        ).consume()

    def _load(self, tx, match, **params):
        return [_to_order(record) for record in tx.run(match + _LOAD, **params)]
