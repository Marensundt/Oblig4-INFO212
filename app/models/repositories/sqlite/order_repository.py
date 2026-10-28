from datetime import date

from app.models.entities import GuestGroup, Order, OrderLine
from app.models.enums import Allergen, OrderStatus, PaymentStatus
from app.models.errors import InvalidStatusTransition, NotFound
from app.models.repositories.interfaces import OrderRepository
from app.models.repositories.sqlite.database import now_iso, parse_datetime


def _placeholders(values):
    return ", ".join("?" for _ in values)


class SqliteOrderRepository(OrderRepository):
    def __init__(self, db):
        self.db = db

    def add(self, order):
        created_at = now_iso()
        with self.db.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")  # lock before choosing the next order number
            order_number = self._next_order_number(conn)
            cursor = conn.execute(
                "INSERT INTO orders (order_number, customer_id, event_date, guest_count, delivery_address,"
                " status, payment_status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (order_number, order.customer_id, order.event_date.isoformat(), order.guest_count,
                 order.delivery_address, OrderStatus(order.status).value,
                 PaymentStatus(order.payment_status).value, created_at, created_at),
            )
            order_id = cursor.lastrowid
            conn.executemany(
                "INSERT INTO order_lines (order_id, food_item_id, item_name, unit_price_nok, quantity)"
                " VALUES (?, ?, ?, ?, ?)",
                [(order_id, line.food_item_id, line.item_name, line.unit_price_nok, line.quantity)
                 for line in order.lines],
            )
            for group in order.guest_groups:
                group_cursor = conn.execute(
                    "INSERT INTO guest_groups (order_id, label, count, dietary_notes) VALUES (?, ?, ?, ?)",
                    (order_id, group.label, group.count, group.dietary_notes),
                )
                conn.executemany(
                    "INSERT INTO guest_group_allergens (guest_group_id, allergen) VALUES (?, ?)",
                    [(group_cursor.lastrowid, Allergen(a).value) for a in group.allergies],
                )
        return self.get(order_id)

    def get(self, order_id):
        with self.db.connect() as conn:
            orders = self._load(conn, "WHERE id = ?", [order_id])
        return orders[0] if orders else None

    def list(self, status=None, date_from=None, date_to=None):
        conditions, params = [], []
        if status is not None:
            conditions.append("status = ?")
            params.append(OrderStatus(status).value)
        if date_from is not None:
            conditions.append("event_date >= ?")
            params.append(date_from.isoformat())
        if date_to is not None:
            conditions.append("event_date <= ?")
            params.append(date_to.isoformat())
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with self.db.connect() as conn:
            return self._load(conn, where, params)

    def list_for_customer(self, customer_id):
        with self.db.connect() as conn:
            return self._load(conn, "WHERE customer_id = ?", [customer_id])

    def update_status(self, order_id, new_status):
        new_status = OrderStatus(new_status)
        with self.db.connect() as conn:
            row = conn.execute("SELECT status FROM orders WHERE id = ?", (order_id,)).fetchone()
            if row is None:
                raise NotFound(f"Order {order_id}")
            current = OrderStatus(row["status"])
            if not current.can_change_to(new_status):
                raise InvalidStatusTransition(current, new_status)
            conn.execute(
                "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
                (new_status.value, now_iso(), order_id),
            )
        return self.get(order_id)

    def update_payment_status(self, order_id, payment_status):
        payment_status = PaymentStatus(payment_status)
        with self.db.connect() as conn:
            cursor = conn.execute(
                "UPDATE orders SET payment_status = ?, updated_at = ? WHERE id = ?",
                (payment_status.value, now_iso(), order_id),
            )
            if cursor.rowcount == 0:
                raise NotFound(f"Order {order_id}")
        return self.get(order_id)

    def _next_order_number(self, conn):
        prefix = f"{date.today():%y}-"
        row = conn.execute(
            "SELECT MAX(CAST(substr(order_number, 4) AS INTEGER)) FROM orders WHERE order_number LIKE ?",
            (prefix + "%",),
        ).fetchone()
        return f"{prefix}{(row[0] or 0) + 1:04d}"

    def _load(self, conn, where_clause, params):
        rows = conn.execute(f"SELECT * FROM orders {where_clause} ORDER BY event_date, id", params).fetchall()
        if not rows:
            return []
        ids = [row["id"] for row in rows]
        in_ids = f"order_id IN ({_placeholders(ids)})"

        lines = {}
        for r in conn.execute(f"SELECT * FROM order_lines WHERE {in_ids} ORDER BY id", ids):
            lines.setdefault(r["order_id"], []).append(
                OrderLine(id=r["id"], food_item_id=r["food_item_id"], item_name=r["item_name"],
                          unit_price_nok=r["unit_price_nok"], quantity=r["quantity"])
            )

        groups, groups_by_id = {}, {}
        for r in conn.execute(f"SELECT * FROM guest_groups WHERE {in_ids} ORDER BY id", ids):
            group = GuestGroup(id=r["id"], label=r["label"], count=r["count"], dietary_notes=r["dietary_notes"])
            groups.setdefault(r["order_id"], []).append(group)
            groups_by_id[group.id] = group
        if groups_by_id:
            group_ids = list(groups_by_id)
            for r in conn.execute(
                f"SELECT guest_group_id, allergen FROM guest_group_allergens"
                f" WHERE guest_group_id IN ({_placeholders(group_ids)})",
                group_ids,
            ):
                groups_by_id[r[0]].allergies.add(Allergen(r[1]))

        return [
            Order(
                id=row["id"],
                order_number=row["order_number"],
                customer_id=row["customer_id"],
                event_date=date.fromisoformat(row["event_date"]),
                guest_count=row["guest_count"],
                delivery_address=row["delivery_address"],
                status=OrderStatus(row["status"]),
                payment_status=PaymentStatus(row["payment_status"]),
                created_at=parse_datetime(row["created_at"]),
                updated_at=parse_datetime(row["updated_at"]),
                lines=lines.get(row["id"], []),
                guest_groups=groups.get(row["id"], []),
            )
            for row in rows
        ]
