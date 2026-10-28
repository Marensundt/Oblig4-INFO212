"""Domain classes (docs/design/domain-class.puml). No storage code here.

`id` is None until the object has been stored by a repository.
"""
from dataclasses import dataclass, field
from datetime import date, datetime

from app.models.enums import Allergen, DietaryLabel, OrderStatus, PaymentStatus, Role
from app.models.errors import InvalidStatusTransition


@dataclass
class User:
    email: str
    password_hash: str
    name: str
    role: Role = Role.CUSTOMER
    phone: str | None = None
    created_at: datetime | None = None
    id: int | None = None

    @property
    def is_admin(self):
        return self.role == Role.ADMIN


@dataclass
class EventCategory:
    slug: str
    name: str
    sort_order: int = 0
    id: int | None = None


@dataclass
class FoodItem:
    name: str
    description: str
    price_nok: int
    min_order_qty: int
    category_ids: list[int] = field(default_factory=list)
    allergens: set[Allergen] = field(default_factory=set)
    dietary_labels: set[DietaryLabel] = field(default_factory=set)
    published: bool = False
    image_filename: str | None = None
    id: int | None = None


@dataclass
class OrderLine:
    """Name and unit price are copied from the food item when the order is submitted."""

    item_name: str
    unit_price_nok: int
    quantity: int
    food_item_id: int | None = None
    id: int | None = None

    @property
    def line_total_nok(self):
        return self.unit_price_nok * self.quantity


@dataclass
class GuestGroup:
    """Allergy and dietary notes per guest group (C3). Deliberately has no guest names (GDPR)."""

    label: str
    count: int
    allergies: set[Allergen] = field(default_factory=set)
    dietary_notes: str = ""
    id: int | None = None


@dataclass
class Order:
    customer_id: int
    event_date: date
    guest_count: int
    delivery_address: str
    lines: list[OrderLine] = field(default_factory=list)
    guest_groups: list[GuestGroup] = field(default_factory=list)
    status: OrderStatus = OrderStatus.SUBMITTED
    payment_status: PaymentStatus = PaymentStatus.NOT_PAID
    order_number: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    id: int | None = None

    @property
    def total_nok(self):
        return sum(line.line_total_nok for line in self.lines)

    def change_status(self, new_status):
        if not self.status.can_change_to(new_status):
            raise InvalidStatusTransition(self.status, new_status)
        self.status = OrderStatus(new_status)


@dataclass
class Question:
    order_id: int
    author_id: int
    text: str
    asked_at: datetime | None = None
    answer_text: str | None = None
    answered_by: int | None = None
    answered_at: datetime | None = None
    id: int | None = None

    @property
    def is_answered(self):
        return self.answer_text is not None
