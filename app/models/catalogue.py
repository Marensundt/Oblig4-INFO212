"""Food item rules for the admin panel (OB4 A1; US-01 – US-03)."""
from dataclasses import replace

from app.models.errors import ItemInUse, NotFound


def delete_food_item(repos, item_id):
    """Delete an item. Items in existing orders are kept so order history stays intact (ASSUMPTION);
    raise ItemInUse so the admin can unpublish instead."""
    if repos.food_items.get(item_id) is None:
        raise NotFound(f"Food item {item_id}")
    if repos.food_items.is_used_in_orders(item_id):
        raise ItemInUse(f"Food item {item_id} is part of an order")
    repos.food_items.delete(item_id)


def set_published(repos, item_id, published):
    item = repos.food_items.get(item_id)
    if item is None:
        raise NotFound(f"Food item {item_id}")
    return repos.food_items.update(replace(item, published=published))
