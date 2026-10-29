"""Fixed value lists of the domain (docs/design/domain-class.puml)."""
from enum import StrEnum


class Role(StrEnum):
    CUSTOMER = "customer"
    ADMIN = "admin"


class OrderStatus(StrEnum):
    """Order status from Oblig 4 A3 (docs/design/state-order.puml)."""

    SUBMITTED = "submitted"
    APPROVED = "approved"
    IN_PREPARATION = "in_preparation"
    DELIVERED = "delivered"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

    @property
    def label(self):
        return self.value.replace("_", " ")

    @property
    def is_final(self):
        return not ALLOWED_TRANSITIONS[self]

    def can_change_to(self, new_status):
        return OrderStatus(new_status) in ALLOWED_TRANSITIONS[self]

    @property
    def next_statuses(self):
        """Statuses this order may change to, in the order of the main path (for the admin form)."""
        return [status for status in OrderStatus if status in ALLOWED_TRANSITIONS[self]]


# OFFICIAL (A3): submitted -> approved -> in_preparation -> delivered, or rejected/cancelled.
# ASSUMPTION (OPEN-9, docs/plans/03): rejected only from submitted; cancelled from any
# non-final state; delivered, rejected and cancelled are final.
ALLOWED_TRANSITIONS = {
    OrderStatus.SUBMITTED: {OrderStatus.APPROVED, OrderStatus.REJECTED, OrderStatus.CANCELLED},
    OrderStatus.APPROVED: {OrderStatus.IN_PREPARATION, OrderStatus.CANCELLED},
    OrderStatus.IN_PREPARATION: {OrderStatus.DELIVERED, OrderStatus.CANCELLED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.REJECTED: set(),
    OrderStatus.CANCELLED: set(),
}


class PaymentStatus(StrEnum):
    """Payment status from Oblig 4 A3. Set freely by the admin (ASSUMPTION, OPEN-9)."""

    NOT_PAID = "not_paid"
    DEPOSIT_PAID = "deposit_paid"
    INVOICED = "invoiced"
    PAID = "paid"

    @property
    def label(self):
        return self.value.replace("_", " ")


class Allergen(StrEnum):
    """The 14 EU allergens (ASSUMPTION: list not given in Oblig 4)."""

    GLUTEN = "gluten"
    CRUSTACEANS = "crustaceans"
    EGGS = "eggs"
    FISH = "fish"
    PEANUTS = "peanuts"
    SOY = "soy"
    MILK = "milk"
    NUTS = "nuts"
    CELERY = "celery"
    MUSTARD = "mustard"
    SESAME = "sesame"
    SULPHITES = "sulphites"
    LUPIN = "lupin"
    MOLLUSCS = "molluscs"

    @property
    def label(self):
        return self.value.capitalize()


class DietaryLabel(StrEnum):
    """Dietary labels (ASSUMPTION: list not given in Oblig 4)."""

    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    LACTOSE_FREE = "lactose_free"
    HALAL = "halal"
    KIDS_FRIENDLY = "kids_friendly"

    @property
    def label(self):
        return self.value.replace("_", "-").capitalize()
