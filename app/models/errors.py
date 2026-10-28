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
