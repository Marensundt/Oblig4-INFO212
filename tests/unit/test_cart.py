"""Cart rules (OB4 C2; US-08, US-09). Pure logic, no database."""
import pytest

from app.models.cart import MAX_QUANTITY, Cart, CartLine, estimated_total_nok
from app.models.entities import FoodItem
from app.models.errors import BelowMinimumOrder, InvalidQuantity, ItemNotAvailable


def item(item_id, name="Fish soup", price=189, minimum=10, published=True):
    return FoodItem(name, "", price, minimum, published=published, id=item_id)


def test_add_at_or_above_minimum():
    # US-08 AC1
    cart = Cart()
    cart.add(item(1), 10)
    assert cart.quantities == {1: 10}


def test_add_below_minimum_is_rejected_with_minimum_in_message():
    # US-08 AC2
    cart = Cart()
    with pytest.raises(BelowMinimumOrder, match="minimum order for “Fish soup” is 10 portions"):
        cart.add(item(1), 9)
    assert len(cart) == 0


@pytest.mark.parametrize("quantity", [0, -5])
def test_zero_or_negative_quantity_is_rejected(quantity):
    with pytest.raises(BelowMinimumOrder):
        Cart().add(item(1, minimum=1), quantity)


def test_adding_same_item_again_adds_quantities():
    # US-08 AC3
    cart = Cart()
    cart.add(item(1), 10)
    cart.add(item(1), 15)
    assert cart.quantities == {1: 25}


def test_quantity_above_maximum_is_rejected():
    cart = Cart()
    cart.add(item(1), MAX_QUANTITY)
    with pytest.raises(InvalidQuantity, match="at most"):
        cart.add(item(1), 10)
    assert cart.quantities == {1: MAX_QUANTITY}


def test_unpublished_item_cannot_be_added():
    with pytest.raises(ItemNotAvailable):
        Cart().add(item(1, published=False), 10)


def test_set_quantity_at_or_above_minimum():
    # US-09 AC2
    cart = Cart({1: 10})
    cart.set_quantity(item(1), 30)
    assert cart.quantities == {1: 30}


def test_set_quantity_below_minimum_keeps_old_quantity():
    # US-09 AC2
    cart = Cart({1: 20})
    with pytest.raises(BelowMinimumOrder):
        cart.set_quantity(item(1), 5)
    assert cart.quantities == {1: 20}


def test_set_quantity_for_item_not_in_cart():
    with pytest.raises(ItemNotAvailable):
        Cart().set_quantity(item(1), 10)


def test_remove():
    # US-09 AC3
    cart = Cart({1: 10, 2: 5})
    cart.remove(1)
    cart.remove(99)  # unknown id is ignored
    assert cart.quantities == {2: 5}


def test_line_total_and_estimated_total():
    # US-09 AC1
    lines = [CartLine(item(1, price=189), 10), CartLine(item(2, "Cake", price=95, minimum=5), 6)]
    assert [line.line_total_nok for line in lines] == [1890, 570]
    assert estimated_total_nok(lines) == 2460
    assert estimated_total_nok([]) == 0


def test_refresh_builds_lines_sorted_by_name():
    cart = Cart({1: 10, 2: 5})
    lines, removed = cart.refresh([item(1, "Fish soup"), item(2, "Apple cake", minimum=5)])
    assert [(line.item.name, line.quantity) for line in lines] == [("Apple cake", 5), ("Fish soup", 10)]
    assert removed == []


def test_refresh_drops_unpublished_and_deleted_items():
    # US-09 AC4
    cart = Cart({1: 10, 2: 10, 3: 10})
    lines, removed = cart.refresh([item(1), item(2, "Rakfisk", published=False)])  # 3 was deleted
    assert [line.item.id for line in lines] == [1]
    assert removed == ["Rakfisk", None]
    assert cart.quantities == {1: 10}


def test_line_below_raised_minimum_is_flagged():
    lines, _ = Cart({1: 10}).refresh([item(1, minimum=20)])
    assert lines[0].below_minimum


def test_session_round_trip_and_bad_data():
    cart = Cart({1: 10})
    assert cart.to_session() == {"1": 10}
    assert Cart.from_session({"1": 10, "x": 3, "2": None}).quantities == {1: 10}
    assert Cart.from_session(None).quantities == {}
