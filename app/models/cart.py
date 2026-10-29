"""Shopping cart rules (OB4 C2; US-08, US-09). Pure logic: no Flask or storage imports.

The cart only holds {food_item_id: quantity}. The controller keeps it in the visitor's session and
passes in food items loaded from the repository, so names and prices are always the current ones.
"""
from dataclasses import dataclass

from app.models.entities import FoodItem
from app.models.errors import BelowMinimumOrder, InvalidQuantity, ItemNotAvailable

# Upper limit per line (ASSUMPTION): stops typing mistakes such as 50000 portions.
MAX_QUANTITY = 9999


@dataclass
class CartLine:
    item: FoodItem
    quantity: int

    @property
    def line_total_nok(self):
        return self.item.price_nok * self.quantity

    @property
    def below_minimum(self):
        """True if the admin raised the minimum order after the item was added."""
        return self.quantity < self.item.min_order_qty


def estimated_total_nok(lines):
    """Estimated, because Ekte Mat confirms the final price when the order is approved (US-09 AC1)."""
    return sum(line.line_total_nok for line in lines)


class Cart:
    def __init__(self, quantities=None):
        self.quantities = dict(quantities or {})

    @classmethod
    def from_session(cls, data):
        """Build a cart from session data ({"<id>": qty}); entries that are not whole numbers are skipped."""
        quantities = {}
        for key, value in (data or {}).items():
            try:
                quantities[int(key)] = int(value)
            except (TypeError, ValueError):
                continue
        return cls(quantities)

    def to_session(self):
        return {str(item_id): quantity for item_id, quantity in self.quantities.items()}

    def __len__(self):
        return len(self.quantities)

    def __contains__(self, item_id):
        return item_id in self.quantities

    @property
    def item_ids(self):
        return list(self.quantities)

    def add(self, item, quantity):
        """Add portions of an item; adding an item that is already in the cart adds the quantities (US-08 AC3)."""
        new_quantity = self.quantities.get(item.id, 0) + quantity
        _check(item, new_quantity)
        self.quantities[item.id] = new_quantity

    def set_quantity(self, item, quantity):
        """Change a line; a rejected change keeps the old quantity (US-09 AC2)."""
        if item.id not in self.quantities:
            raise ItemNotAvailable(f"“{item.name}” is not in the cart.")
        _check(item, quantity)
        self.quantities[item.id] = quantity

    def remove(self, item_id):
        self.quantities.pop(item_id, None)

    def refresh(self, items):
        """Match the cart against the current food items.

        Returns (lines, removed): lines in item name order, and the names of items that were removed
        because they were unpublished (US-09 AC4); deleted items are removed too but have no name.
        """
        by_id = {item.id: item for item in items}
        lines, removed = [], []
        for item_id, quantity in list(self.quantities.items()):
            item = by_id.get(item_id)
            if item is None or not item.published:
                del self.quantities[item_id]
                removed.append(item.name if item else None)
            else:
                lines.append(CartLine(item, quantity))
        lines.sort(key=lambda line: line.item.name.lower())
        return lines, removed


def _check(item, quantity):
    if not item.published:
        raise ItemNotAvailable(f"“{item.name}” is not on the menu.")
    if quantity < item.min_order_qty:
        raise BelowMinimumOrder(item)
    if quantity > MAX_QUANTITY:
        raise InvalidQuantity(f"You can order at most {MAX_QUANTITY} portions of “{item.name}”.")
