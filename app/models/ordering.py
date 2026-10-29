"""Placing an order from the cart (OB4 C3; US-12, US-13). No Flask imports.

All order rules are checked here, so the controller only maps form fields and error messages.
"""
from datetime import date

from app.models.cart import Cart
from app.models.entities import Order, OrderLine
from app.models.enums import OrderStatus, PaymentStatus
from app.models.errors import InvalidOrder

# Most guest groups per order (ASSUMPTION): keeps the form usable.
MAX_GUEST_GROUPS = 20


def check_cart(repos, cart):
    """Return the cart lines if the cart can be ordered, otherwise raise InvalidOrder (key "cart").

    Works on a copy, so the caller's cart is unchanged.
    """
    copy = Cart(cart.quantities)
    lines, removed = copy.refresh(repos.food_items.get_many(copy.item_ids))
    if removed:
        raise InvalidOrder({"cart": "Some items in your cart are no longer on the menu. Check your cart."})
    if not lines:
        raise InvalidOrder({"cart": "Your cart is empty."})
    below = [line.item.name for line in lines if line.below_minimum]
    if below:
        # OB4 C2: the minimum order may have been raised after the item was added
        raise InvalidOrder({"cart": f"Below the minimum order: {', '.join(below)}. Check your cart."})
    return lines


def place_order(repos, customer, cart, event_date, guest_count, delivery_address, guest_groups, today=None):
    """Store the cart as a new order with status submitted and payment status not paid (US-12 AC1).

    Names and prices are copied onto the order lines, so later menu changes do not change the order
    (US-02 AC2). No payment step (OB4 C3, US-12 AC4). Raises InvalidOrder with all broken rules.
    """
    lines = check_cart(repos, cart)
    today = today or date.today()
    errors = {}
    if event_date <= today:
        errors["event_date"] = "The event date must be after today."  # DV-04 (ASSUMPTION)
    if guest_count < 1:
        errors["guest_count"] = "The number of guests must be at least 1."  # DV-01 (ASSUMPTION)
    if not delivery_address.strip():
        errors["delivery_address"] = "Enter a delivery address."
    errors.update(_check_guest_groups(guest_groups, guest_count))
    if errors:
        raise InvalidOrder(errors)

    order = Order(
        customer_id=customer.id,
        event_date=event_date,
        guest_count=guest_count,
        delivery_address=delivery_address.strip(),
        lines=[OrderLine(line.item.name, line.item.price_nok, line.quantity, food_item_id=line.item.id)
               for line in lines],
        guest_groups=guest_groups,
        status=OrderStatus.SUBMITTED,
        payment_status=PaymentStatus.NOT_PAID,
    )
    return repos.orders.add(order)


def _check_guest_groups(groups, guest_count):
    if not groups:
        return {"guest_groups": "Add at least one guest group."}  # DV-11 (ASSUMPTION)
    if len(groups) > MAX_GUEST_GROUPS:
        return {"guest_groups": f"Use at most {MAX_GUEST_GROUPS} guest groups."}
    if any(not group.label.strip() for group in groups):
        return {"guest_groups": "Every guest group needs a name, e.g. “Adults” or “Children”."}
    if any(group.count < 1 for group in groups):
        return {"guest_groups": "Every guest group needs at least 1 guest."}
    total = sum(group.count for group in groups)
    if total > guest_count:
        # US-13 AC2 (ASSUMPTION)
        return {"guest_groups": f"The guest groups add up to {total} guests, "
                                f"but the order is for {guest_count}."}
    return {}
