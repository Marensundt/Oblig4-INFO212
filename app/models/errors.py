"""Domain errors. Repositories raise these instead of storage-specific exceptions."""


class DomainError(Exception):
    pass


class NotFound(DomainError):
    pass


class InvalidStatusTransition(DomainError):
    def __init__(self, current, new):
        super().__init__(f"Order status cannot change from {current} to {new}")
        self.current = current
        self.new = new


class DuplicateEmail(DomainError):
    pass


class DataIntegrityError(DomainError):
    """A stored value breaks a data rule (e.g. price <= 0, unknown status)."""


class ItemInUse(DomainError):
    """A food item that is part of an order cannot be deleted (US-03 AC2)."""


class StorageNotInitialised(DomainError):
    """The database has not been created yet (run `flask --app run reset-db --yes`)."""


class InvalidQuantity(DomainError):
    """A cart quantity is outside the allowed range (OB4 C2). The message is shown to the visitor."""


class BelowMinimumOrder(InvalidQuantity):
    """Quantity below the food item's minimum order (OB4 C2; US-08 AC2, US-09 AC2)."""

    def __init__(self, item):
        super().__init__(f"The minimum order for “{item.name}” is {item.min_order_qty} portions.")
        self.item = item


class ItemNotAvailable(DomainError):
    """The food item does not exist or is not published, so it cannot be in the cart."""


class InvalidOrder(DomainError):
    """The order breaks one or more order rules (C3; US-12, US-13).

    `errors` maps a field ("event_date", "guest_count", "guest_groups", "cart") to a message for the customer.
    """

    def __init__(self, errors):
        super().__init__("; ".join(errors.values()))
        self.errors = errors
