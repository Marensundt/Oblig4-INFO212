"""Delete and publish rules for food items (US-03)."""
import pytest

from app.models.catalogue import delete_food_item, set_published
from app.models.errors import ItemInUse, NotFound
from tests.factories import make_order


def test_delete_unused_item(repos, soup):
    delete_food_item(repos, soup.id)
    assert repos.food_items.get(soup.id) is None


def test_delete_item_in_order_is_refused(repos, soup, customer):
    repos.orders.add(make_order(customer.id, soup))
    with pytest.raises(ItemInUse):
        delete_food_item(repos, soup.id)
    assert repos.food_items.get(soup.id) is not None


def test_delete_missing_item(repos):
    with pytest.raises(NotFound):
        delete_food_item(repos, 999)


def test_set_published_keeps_other_fields(repos, soup):
    hidden = set_published(repos, soup.id, False)
    assert hidden.published is False
    assert (hidden.name, hidden.price_nok, hidden.allergens) == (soup.name, soup.price_nok, soup.allergens)
    assert set_published(repos, soup.id, True).published is True
    with pytest.raises(NotFound):
        set_published(repos, 999, True)
