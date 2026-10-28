"""Helpers for building test data."""
from datetime import date, timedelta

from app.models.entities import GuestGroup, Order, OrderLine
from app.models.enums import Allergen


def make_order(customer_id, food_item, days_ahead=30, guests=20, **kwargs):
    return Order(
        customer_id=customer_id,
        event_date=date.today() + timedelta(days=days_ahead),
        guest_count=guests,
        delivery_address="Bryggen 1, 5003 Bergen",
        lines=[OrderLine(food_item.name, food_item.price_nok, guests, food_item_id=food_item.id)],
        guest_groups=[GuestGroup("Adults", guests, {Allergen.NUTS}, "1 vegetarian")],
        **kwargs,
    )
