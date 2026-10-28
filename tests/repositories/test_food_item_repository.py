from dataclasses import replace

import pytest

from app.models.entities import FoodItem
from app.models.enums import Allergen, DietaryLabel
from app.models.errors import DataIntegrityError, NotFound
from tests.factories import make_order


def test_add_and_get_round_trip(repos, categories):
    item = repos.food_items.add(FoodItem(
        "Beetroot salad", "Hardanger goat cheese", 165, 10,
        category_ids=[categories["birthday"].id, categories["conference"].id],
        allergens={Allergen.MILK, Allergen.MUSTARD},
        dietary_labels={DietaryLabel.VEGETARIAN},
        published=True,
        image_filename="salad.png",
    ))
    stored = repos.food_items.get(item.id)
    assert stored == item
    assert stored.category_ids == [categories["birthday"].id, categories["conference"].id]
    assert stored.allergens == {Allergen.MILK, Allergen.MUSTARD}
    assert stored.dietary_labels == {DietaryLabel.VEGETARIAN}


def test_update_replaces_fields_and_relations(repos, soup, categories):
    changed = replace(soup, price_nok=199, allergens={Allergen.FISH}, category_ids=[categories["wedding"].id],
                      published=False)
    updated = repos.food_items.update(changed)
    assert updated.price_nok == 199
    assert updated.allergens == {Allergen.FISH}
    assert updated.category_ids == [categories["wedding"].id]
    assert updated.published is False


def test_update_missing_item_raises(repos, soup):
    with pytest.raises(NotFound):
        repos.food_items.update(replace(soup, id=999))


def test_delete(repos, soup):
    repos.food_items.delete(soup.id)
    assert repos.food_items.get(soup.id) is None
    with pytest.raises(NotFound):
        repos.food_items.delete(soup.id)


def test_get_many_and_list_all(repos, soup, categories):
    salad = repos.food_items.add(FoodItem("Anchovy salad", "", 150, 5, category_ids=[categories["birthday"].id]))
    assert {i.id for i in repos.food_items.get_many([soup.id, salad.id, 999])} == {soup.id, salad.id}
    assert repos.food_items.get_many([]) == []
    assert [i.name for i in repos.food_items.list_all()] == ["Anchovy salad", "Fish soup"]


def test_list_published_by_category(repos, soup, categories):
    # C1: published items grouped by event; an item in two categories appears in both
    both = repos.food_items.add(FoodItem(
        "Lamb", "", 245, 10, category_ids=[categories["birthday"].id, categories["conference"].id], published=True,
    ))
    repos.food_items.add(FoodItem("Rakfisk", "", 210, 10, category_ids=[categories["wedding"].id], published=False))

    groups = {category.slug: [item.name for item in items]
              for category, items in repos.food_items.list_published_by_category()}

    assert groups == {"birthday": ["Lamb"], "conference": ["Fish soup", "Lamb"]}
    assert both.id is not None


def test_is_used_in_orders(repos, soup, customer):
    assert not repos.food_items.is_used_in_orders(soup.id)
    repos.orders.add(make_order(customer.id, soup))
    assert repos.food_items.is_used_in_orders(soup.id)


def test_deleting_used_item_keeps_order_history(repos, soup, customer):
    order = repos.orders.add(make_order(customer.id, soup))
    repos.food_items.delete(soup.id)
    line = repos.orders.get(order.id).lines[0]
    assert line.food_item_id is None
    assert line.item_name == "Fish soup"


@pytest.mark.parametrize("price,min_order", [(0, 1), (-5, 1), (100, 0)])
def test_invalid_price_or_min_order_refused(repos, price, min_order):
    # Price > 0 (DV-03, ASSUMPTION); min order >= 1 (needed for C2)
    with pytest.raises(DataIntegrityError):
        repos.food_items.add(FoodItem("Bad", "", price, min_order))
    assert repos.food_items.list_all() == []
